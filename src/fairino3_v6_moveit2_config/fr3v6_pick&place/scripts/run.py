#!/usr/bin/env python3
import rclpy
from robot_movement import RobotMover


def main():
    rclpy.init()
    robot = RobotMover()

    # ──────────────────────────────────────────
    #  Set target group: 'r', 'b', or 'g'
    # ──────────────────────────────────────────
    target = 'g'

    robot.run_sequence(target)

    robot.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()