#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import xmlrpc.client
import time

class FairinoDOToggleNode(Node):
    def _init_(self):
        super()._init_('fairino_do_toggle_node')
        # XML-RPC client to communicate with Fairino robot
        self.robot_proxy = xmlrpc.client.ServerProxy('http://192.168.58.2:20003/RPC2')
        self.get_logger().info('Connected to Fairino robot via XML-RPC')

        # Parameters
        self.do_id = 1  # Digital output ID (DO[3] from your logs)
        self.toggle_interval = 0.01  # 5 seconds
        self.do_state = 1  # Start with ON (1 = ON, 0 = OFF)

        # Timer to toggle DO every 5 seconds
        self.timer = self.create_timer(self.toggle_interval, self.toggle_do_callback)

        # Enable the robot
        self.enable_robot()

    def enable_robot(self):
        """Enable the robot using RobotEnable API."""
        try:
            result = self.robot_proxy.RobotEnable(1)
            self.get_logger().info('Robot enabled')
            return result
        except Exception as e:
            self.get_logger().error(f'Failed to enable robot: {e}')
            return -1

    def toggle_do_callback(self):
        """Toggle digital output using SetDO API."""
        try:
            # Ensure correct types
            do_id = int(self.do_id)
            do_state = int(self.do_state)
            smooth = 0  # Not smooth
            block = 0   # Non-blocking
            self.get_logger().info(f'Attempting SetDO with id={do_id}, state={do_state}, smooth={smooth}, block={block}')

            # Call SetDO with all four parameters
            result = self.robot_proxy.SetDO(do_id, do_state, smooth, block)
            state_str = "ON" if do_state else "OFF"
            self.get_logger().info(f'SetDO({do_id}, {do_state}, {smooth}, {block}) - DO[{do_id}] turned {state_str}, result: {result}')
            
            # Toggle state for next iteration
            self.do_state = 1 - self.do_state  # Switch between 1 and 0
        except xmlrpc.client.Fault as fault:
            self.get_logger().error(f'SetDO failed with fault: {fault}')
            # Attempt reconnection
            self.get_logger().info('Attempting to reconnect...')
            try:
                self.robot_proxy = xmlrpc.client.ServerProxy('http://192.168.58.2:20003/RPC2')
                self.get_logger().info('Reconnected to Fairino robot')
            except Exception as reconnect_e:
                self.get_logger().error(f'Reconnection failed: {reconnect_e}')
        except Exception as e:
            self.get_logger().error(f'Failed to set DO[{self.do_id}]: {e}')

def main():
    rclpy.init()
    node = FairinoDOToggleNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down DO toggle node')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '_main_':
    main()