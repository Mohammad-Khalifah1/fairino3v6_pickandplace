# Fairino3 V6 — Color-Based Pick & Place

Autonomous pick-and-place system using a **Fairino FR3 V6** robot arm. A USB camera detects the color of an object (red, green, or blue), and the robot picks it up and places it in the corresponding location.

---

## System Overview

```
Camera (OpenCV)
    └── detect color → stable for 3s
            └── confirmed_color.set()
                    └── run_sequence(r / g / b)
                            ├── MoveIt2 plans each joint move
                            ├── fairino3_controller executes trajectory
                            └── Gripper via XML-RPC (SetDO)
```
<img width="2908" height="1440" alt="Gemini_Generated_Image_vn9diqvn9diqvn9d" src="https://github.com/user-attachments/assets/69d938b4-a107-47a8-8889-523d7b87bbb2" />

---

## Project Structure

```
fairino3_v6_moveit2_config/
├── config/
│   ├── fairino3_v6_robot.urdf.xacro       # Robot description
│   ├── fairino3_v6_robot.srdf             # Planning groups & end-effectors
│   ├── fairino3_v6_robot.ros2_control.xacro
│   ├── moveit_controllers.yaml            # MoveIt controller config
│   ├── ros2_controllers.yaml              # ROS2 controller config
│   ├── kinematics.yaml                    # IK solver settings
│   ├── joint_limits.yaml
│   ├── initial_positions.yaml
│   └── pilz_cartesian_limits.yaml
│
├── launch/
│   ├── demo.launch.py                     # Full system launch (MoveIt + RViz)
│   ├── move_group.launch.py               # MoveIt move_group node only
│   ├── moveit_rviz.launch.py              # RViz with MoveIt plugin
│   ├── spawn_controllers.launch.py        # Load ros2_controllers
│   └── rsp.launch.py                      # Robot state publisher
│
├── fr3v6_pick&place/scripts/
│   ├── run_main.py                        # ← Main entry point
│   ├── color_detection.py                 # Camera + HSV color detection
│   ├── robot_movement.py                  # ROS2 node, MoveIt planning, sequences
│   ├── gripper.py                         # XML-RPC gripper control
│
└── world_collision.py                     # Collision objects setup
```

---

## Dependencies

| Dependency | Version |
|---|---|
| ROS2 | Humble |
| MoveIt2 | Humble |
| Python | 3.10+ |
| OpenCV | `pip install opencv-python` |
| NumPy | `pip install numpy` |
| Robot IP | `192.168.58.2:20003` (XML-RPC) |

---

## How It Works

### 1. Color Detection (`color_detection.py`)

- Captures frames from USB camera (index `2`)
- Converts BGR → HSV and applies color masks:

| Color | H range | S range | V range |
|---|---|---|---|
| RED | 0–8 | 150–255 | 120–255 |
| GREEN | 45–85 | 80–255 | 80–255 |
| BLUE | 100–140 | 150–255 | 0–255 |

- Returns the color with the largest contour area (minimum 800 px²)

### 2. Stability Check (`run_main.py`)

- The same color must be detected **continuously for 3 seconds**
- If the color changes mid-detection, the timer resets
- Once confirmed → `confirmed_color.set()` signals the robot thread
- **During robot motion, all new color detections are ignored**

### 3. Robot Sequences (`robot_movement.py`)

All three sequences share the same **pick positions**. Only the **place positions** differ.

#### Pick (shared across all colors)

| Step | Position | Joints [j1..j6] ° | Action |
|---|---|---|---|
| 1 | `home_pos` | 108, -107, 97, -80, -90, -26 | — |
| 2 | `prepickpos` | 65, -71, 76, -98, -91, 24 | — |
| 3 | `pickpos` | 63, -63, 86, -114, -90, 20 | ✊ close gripper |
| 4 | `postpickpos` | 65, -71, 76, -98, -91, 24 | — |

#### Place — Red

| Step | Position | Joints [j1..j6] ° | Action |
|---|---|---|---|
| 5 | `rprepos` | 118, -73, 75, -92, -90, -16 | — |
| 6 | `rpos` | 120, -68, 93, -115, -90, -15 | ✋ open gripper |
| 7 | `rpostpos` | 118, -73, 75, -92, -90, -16 | — |
| 8 | `home_pos` | 108, -107, 97, -80, -90, -26 | — |

#### Place — Green

| Step | Position | Joints [j1..j6] ° | Action |
|---|---|---|---|
| 5 | `gprepos` | 130, -71, 76, -94, -92, -6 | — |
| 6 | `gpos` | 132, -66, 91, -114, -92, -6 | ✋ open gripper |
| 7 | `gpostpos` | 130, -71, 76, -94, -92, -6 | — |
| 8 | `home_pos` | 108, -107, 97, -80, -90, -26 | — |

#### Place — Blue

| Step | Position | Joints [j1..j6] ° | Action |
|---|---|---|---|
| 5 | `bprepos` | 110, -70, 75, -96, -90, -28 | — |
| 6 | `bpos` | 110, -65, 88, -113, -90, -28 | ✋ open gripper |
| 7 | `bpostpos` | 110, -70, 75, -96, -90, -28 | — |
| 8 | `home_pos` | 108, -107, 97, -80, -90, -26 | — |

### 4. Gripper (`gripper.py`)

Controls the gripper via XML-RPC to the robot controller:

```
close → SetDO(0, 1)   # DO[0] = ON
open  → SetDO(0, 0)   # DO[0] = OFF
```

### 5. Motion Planning

Each `move_to()` call:
- Builds a `GetMotionPlan` request for planning group `fairino3_v6_group`
- Allows up to **3 planning attempts**, 10 seconds each
- Velocity scaling: `0.3` | Acceleration scaling: `0.3`
- Sends the trajectory to `fairino3_controller/follow_joint_trajectory`
- Blocks until execution is complete before moving to the next step

---

## Running the System

### Launch MoveIt

```bash
ros2 launch fairino3_v6_moveit2_config demo.launch.py
```

### Run the sorting system

```bash
cd fr3v6_pick&place/scripts/
python3 run_main.py
```

### Test a single color manually

```bash
# Edit run.py and set target = 'r' / 'g' / 'b'
python3 run.py
```

Press `ESC` in the camera window to stop.

---

## Configuration

| Parameter | Location | Default |
|---|---|---|
| Camera index | `color_detection.py` line 20 | `2` |
| Detection duration | `run_main.py` | `3.0s` |
| Robot IP | `gripper.py` | `192.168.58.2` |
| Robot port | `gripper.py` | `20003` |
| Velocity scaling | `robot_movement.py` | `0.3` |
| Planning attempts | `robot_movement.py` | `3` |
| Planning timeout | `robot_movement.py` | `10s` |

---

## Notes

- The gripper opens automatically on startup
- Pre/post positions exist to ensure collision-free approach and retreat
- The camera thread runs as a **daemon** — it dies automatically when the main process exits
- New color detections are silently discarded while the robot is executing a sequence
