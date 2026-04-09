#!/usr/bin/env python3
"""
Main entry point — Color detection + Pick-and-place orchestration.
"""

import time
import threading
import cv2
import rclpy

import color_detection
from color_detection import detect_color
from robot_movement import RobotMover

# ── Config ────────────────────────────────────────────────────────────────────
DETECTION_DURATION = 3.0
COLOR_TO_GROUP     = {'RED': 'r', 'GREEN': 'g', 'BLUE': 'b'}

# ── Shared state between camera thread and main thread ────────────────────────
confirmed_color = threading.Event()
confirmed_group = None


def camera_thread(cap):
    """Runs forever: shows live feed and signals when a color is confirmed."""
    global confirmed_group

    current_color = None
    start_time    = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print('[WARN] Camera read failed — retrying...')
            continue

        detected = detect_color(frame)

        cv2.putText(frame, detected, (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow('Color Detection', frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

        # Only do detection logic when robot is idle (event not yet set)
        if confirmed_color.is_set():
            current_color = None
            start_time    = None
            continue

        if detected == 'NONE':
            current_color = None
            start_time    = None
        elif detected != current_color:
            current_color = detected
            start_time    = time.time()
        elif time.time() - start_time >= DETECTION_DURATION:
            group = COLOR_TO_GROUP.get(current_color)
            if group:
                print(f'[INFO] Confirmed color: {current_color} → group: {group}')
                confirmed_group = group
                confirmed_color.set()
            current_color = None
            start_time    = None

    cap.release()
    cv2.destroyAllWindows()


def main():
    cap = color_detection.cap
    if not cap.isOpened():
        raise RuntimeError('Cannot open camera')

    rclpy.init()
    robot = RobotMover()

    # Start camera in its own thread (daemon = dies with main)
    t_cam = threading.Thread(target=camera_thread, args=(cap,), daemon=True)
    t_cam.start()

    print('[INFO] System ready — starting sorting loop. Press ESC to stop.')

    try:
        while rclpy.ok():
            confirmed_color.wait()                      # block until color confirmed
            group = confirmed_group

            t_robot = threading.Thread(target=robot.run_sequence, args=(group,))
            t_robot.start()
            t_robot.join()                              # wait for robot to finish

            confirmed_color.clear()                     # discard any detection during movement

    except KeyboardInterrupt:
        print('[INFO] Shutting down.')
    finally:
        robot.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()