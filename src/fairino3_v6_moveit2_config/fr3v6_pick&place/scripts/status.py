#!/usr/bin/env python3
import xmlrpc.client


class Status:
    DO_MAP = {
        'r': 1,
        'b': 2,
        'g': 3,
    }

    def __init__(self, ip='192.168.58.2', port=20003):
        self.url = f'http://{ip}:{port}/RPC2'
        self.robot_proxy = xmlrpc.client.ServerProxy(self.url)
        print(f'[INFO] Status connected to {self.url}')
        self.all_off()

    def _set_do(self, do_id, state):
        try:
            result = self.robot_proxy.SetDO(int(do_id), int(state), 0, 0)
            state_str = "ON" if state else "OFF"
            print(f'[INFO] Status DO[{do_id}] -> {state_str}, result: {result}')
            return result
        except Exception as e:
            print(f'[ERROR] Status SetDO failed: {e}')
            return -1

    def all_off(self):
        for do_id in self.DO_MAP.values():
            self._set_do(do_id, 0)

    def on(self, group):
        do_id = self.DO_MAP.get(group)
        if do_id:
            self._set_do(do_id, 1)

    def off(self, group):
        do_id = self.DO_MAP.get(group)
        if do_id:
            self._set_do(do_id, 0)
