import os
from pathlib import Path
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.substitutions import Command, LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    # Paths to share directories
    fairino_description_path = get_package_share_directory('fairino_description')
    fairino5_v6_moveit2_config_path = get_package_share_directory('fairino_description')

    # Path to URDF and controllers YAML file
    urdf_file = os.path.join(fairino_description_path, 'urdf', 'fr5v6_igazebo.urdf')
    controllers_file = os.path.join(fairino5_v6_moveit2_config_path, 'config', 'gazebo_controller.yaml')

    # Gazebo resource path
    gazebo_resource_path = SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH",
        value=[str(Path(fairino_description_path).parent.resolve())]
    )

    # Robot description
    robot_description = ParameterValue(
        Command(['xacro ', urdf_file]),
        value_type=str
    )

    # Nodes
    # Robot State Publisher
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{"robot_description": robot_description, "use_sim_time": True}],
    )

    # Gazebo Simulation
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory("ros_gz_sim"), "launch", "gz_sim.launch.py")
        ]),
        launch_arguments={"gz_args": "-v 4 -r empty.sdf"}.items()
    )

    # Spawn the robot in Gazebo
    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-topic", "robot_description",
            "-name", "fairino5_v6_robot"
        ]
    )

    # ROS 2 Control Node
    ros2_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        output="screen",
        parameters=[controllers_file],
        remappings=[
            ('/controller_manager/robot_description', '/robot_description'),
        ]
    )

    # Joint State Broadcaster
    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
        output="screen",
    )

    # Fairino5 Controller
    fr5v6_arm_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=['fr5v6_arm_controller', '--controller-manager', '/controller_manager'],
        output="screen",
    )

    # Fairino5 Controller
    gripper_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=['gripper_controller', '--controller-manager', '/controller_manager'],
        output="screen",
    )

    # ROS 2 - Gazebo Bridge
    gz_ros2_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"
        ],
        output="screen",
    )

    # Launch Description
    return LaunchDescription([
        gazebo_resource_path,
        gazebo,
        robot_state_publisher_node,
        gz_spawn_entity,
        ros2_control_node,
        joint_state_broadcaster,
        fr5v6_arm_controller,
        gripper_controller,
        gz_ros2_bridge,
    ])
