#!/usr/bin/env python3
import xmlrpc.client
import time


class Gripper:
    def __init__(self, ip='192.168.58.2', port=20003):
        self.url = f'http://{ip}:{port}/RPC2'
        self.robot_proxy = xmlrpc.client.ServerProxy(self.url)

        self.do_id = 0
        print(f'[INFO] Connected to Fairino robot at {self.url}')

        self.enable_robot()

    def enable_robot(self):
        try:
            result = self.robot_proxy.RobotEnable(1)
            print('[INFO] Robot enabled')
            return result
        except Exception as e:
            print(f'[ERROR] Failed to enable robot: {e}')
            return -1

    def set_do(self, state):
        try:
            do_id = int(self.do_id)
            do_state = int(state)
            smooth = 0
            block = 0

            result = self.robot_proxy.SetDO(do_id, do_state, smooth, block)

            state_str = "ON" if do_state else "OFF"
            print(f'[INFO] DO[{do_id}] -> {state_str}, result: {result}')

            return result

        except Exception as e:
            print(f'[ERROR] SetDO failed: {e}')
            return -1

    def open_gripper(self):
        return self.set_do(0)

    def close_gripper(self):
        return self.set_do(1)