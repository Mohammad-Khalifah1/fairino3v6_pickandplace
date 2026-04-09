#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from control_msgs.action import FollowJointTrajectory
from moveit_msgs.srv import GetMotionPlan
from moveit_msgs.msg import RobotState, Constraints, JointConstraint
from sensor_msgs.msg import JointState
import numpy as np
import time

from gripper import Gripper  # External gripper class


# ──────────────────────────────────────────────────────────────────────────────
#  POSITIONS  [j1, j2, j3, j4, j5, j6] in degrees
# ──────────────────────────────────────────────────────────────────────────────
POSITIONS = {
    'home_pos':      [108.0, -107.0, 97.0, -80.0, -90.0, -26.0],

    # Shared pick positions (same for all groups)
    'prepickpos':    [65.0, -71.0, 76.0, -98.0, -91.0, 24.0],
    'pickpos':       [63.0, -63.0, 86.0, -114.0, -90.0, 20.0],
    'postpickpos':   [65.0, -71.0, 76.0, -98.0, -91.0, 24.0],

    # R group — place positions
    'rprepos':       [118.0, -73.0, 75.0, -92.0, -90.0, -16.0],
    'rpos':          [120.0, -68.0, 93.0, -115.0, -90.0, -15.0],
    'rpostpos':      [118.0, -73.0, 75.0, -92.0, -90.0, -16.0],

    # B group — place positions
    'bprepos':       [110.0, -70.0, 75.0, -96.0, -90.0, -28.0],
    'bpos':          [110.0, -65.0, 88.0, -113.0, -90.0, -28.0],
    'bpostpos':      [110.0, -70.0, 75.0, -96.0, -90.0, -28.0],

    # G group — place positions
    'gprepos':       [130.0, -71.0, 76.0, -94.0, -92.0, -6.0],
    'gpos':          [132.0, -66.0, 91.0, -114.0, -92.0, -6.0],
    'gpostpos':      [130.0, -71.0, 76.0, -94.0, -92.0, -6.0],
}


# ──────────────────────────────────────────────────────────────────────────────
#  SEQUENCES
#  Each step is either:
#    'position_name'               → just move
#    ('position_name', 'action')   → move then trigger gripper
#
#  Gripper actions: 'open' | 'close'
# ──────────────────────────────────────────────────────────────────────────────
SEQUENCES = {
    'r': [
        'home_pos',
        'prepickpos',
        ('pickpos',    'close'),   # Pick up object
        'postpickpos',
        'rprepos',
        ('rpos',       'open'),    # Place object
        'rpostpos',
        'home_pos',
    ],
    'b': [
        'home_pos',
        'prepickpos',
        ('pickpos',    'close'),   # Pick up object
        'postpickpos',
        'bprepos',
        ('bpos',       'open'),    # Place object
        'bpostpos',
        'home_pos',
    ],
    'g': [
        'home_pos',
        'prepickpos',
        ('pickpos',    'close'),   # Pick up object
        'postpickpos',
        'gprepos',
        ('gpos',       'open'),    # Place object
        'gpostpos',
        'home_pos',
    ],
}


# ──────────────────────────────────────────────────────────────────────────────
#  RobotMover
# ──────────────────────────────────────────────────────────────────────────────
class RobotMover(Node):
    def __init__(self):
        super().__init__('robot_mover_node')

        self.controller_name = 'fairino3_controller'
        self.joint_names     = ['j1', 'j2', 'j3', 'j4', 'j5', 'j6']
        self.group_name      = 'fairino3_v6_group'   # Must match SRDF planning group

        self.velocity_scaling     = 0.3
        self.acceleration_scaling = 0.3
        self.is_moving            = False

        self.positions = {name: {'angles': angles} for name, angles in POSITIONS.items()}
        self.gripper   = Gripper()

        # Action client — sends trajectory to controller
        self._action_client = ActionClient(
            self, FollowJointTrajectory,
            f'/{self.controller_name}/follow_joint_trajectory'
        )
        self._action_client.wait_for_server()

        # Service client — requests motion plan from MoveIt
        self.planning_client = self.create_client(GetMotionPlan, 'plan_kinematic_path')
        while not self.planning_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for planning service...')

        # Subscribe to joint states
        self.current_joint_state = None
        self.create_subscription(JointState, 'joint_states', self._joint_state_callback, 10)

        # Wait for first joint state (max 5 s)
        start = self.get_clock().now().to_msg().sec
        while self.current_joint_state is None and rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.1)
            if self.get_clock().now().to_msg().sec - start > 5.0:
                raise RuntimeError('No joint state received within 5 seconds')

        # Always ensure gripper is open on startup
        self.get_logger().info('Startup: opening gripper')
        self.gripper.open_gripper()

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _joint_state_callback(self, msg):
        self.current_joint_state = msg

    def _goal_response_callback(self, future, position_name):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error(f'Goal rejected: {position_name}')
            self.is_moving = False
            return
        goal_handle.get_result_async().add_done_callback(
            lambda f: self._result_callback(f, position_name)
        )

    def _result_callback(self, future, position_name):
        self.get_logger().info(f'Reached: {position_name}')
        self.is_moving = False

    # ── Core movement ──────────────────────────────────────────────────────────

    def move_to(self, position_name):
        """Plan and execute motion to a named position. Returns True on success."""
        if self.is_moving:
            self.get_logger().warn('Already moving — ignoring request.')
            return False

        position = self.positions.get(position_name)
        if not position:
            self.get_logger().error(f'Unknown position: {position_name}')
            return False

        target_angles = [np.deg2rad(a) for a in position['angles']]
        self.is_moving = True
        self.get_logger().info(f'Moving to: {position_name}')

        for attempt in range(1, 4):
            request = GetMotionPlan.Request()
            request.motion_plan_request.group_name                      = self.group_name
            request.motion_plan_request.num_planning_attempts           = 20
            request.motion_plan_request.allowed_planning_time           = 10.0
            request.motion_plan_request.max_velocity_scaling_factor     = self.velocity_scaling
            request.motion_plan_request.max_acceleration_scaling_factor = self.acceleration_scaling

            start_state = RobotState()
            start_state.joint_state = self.current_joint_state
            request.motion_plan_request.start_state = start_state

            constraints = Constraints()
            for joint_name, angle in zip(self.joint_names, target_angles):
                jc = JointConstraint()
                jc.joint_name      = joint_name
                jc.position        = angle
                jc.tolerance_above = 0.002
                jc.tolerance_below = 0.002
                jc.weight          = 1.0
                constraints.joint_constraints.append(jc)
            request.motion_plan_request.goal_constraints.append(constraints)

            future = self.planning_client.call_async(request)
            rclpy.spin_until_future_complete(self, future)

            result = future.result()
            if result is not None and result.motion_plan_response.error_code.val == 1:
                trajectory = result.motion_plan_response.trajectory.joint_trajectory
                goal_msg = FollowJointTrajectory.Goal()
                goal_msg.trajectory = trajectory
                send_future = self._action_client.send_goal_async(goal_msg)
                send_future.add_done_callback(
                    lambda f: self._goal_response_callback(f, position_name)
                )
                return True

            self.get_logger().error(f'Planning attempt {attempt}/3 failed for: {position_name}')

        self.get_logger().error(f'All planning attempts failed for: {position_name}')
        self.is_moving = False
        return False

    def wait_until_done(self):
        """Block until the current movement finishes."""
        while self.is_moving and rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.1)

    # ── Sequence runner ────────────────────────────────────────────────────────

    def run_sequence(self, group):
        """
        Execute the full pick-and-place sequence for a group ('r', 'b', or 'g').
        Each step can be a position name or a (position_name, gripper_action) tuple.
        """
        sequence = SEQUENCES.get(group)
        if not sequence:
            self.get_logger().error(f'Unknown group: "{group}". Available: {list(SEQUENCES.keys())}')
            return

        self.get_logger().info(f'Starting sequence for group: {group}')

        for step in sequence:
            position_name, gripper_action = step if isinstance(step, tuple) else (step, None)

            self.move_to(position_name)
            self.wait_until_done()

            if gripper_action == 'open':
                self.get_logger().info('Gripper: opening')
                self.gripper.open_gripper()
                time.sleep(0.3)
            elif gripper_action == 'close':
                self.get_logger().info('Gripper: closing')
                self.gripper.close_gripper()
                time.sleep(0.3)

        self.get_logger().info(f'Sequence complete for group: {group}')