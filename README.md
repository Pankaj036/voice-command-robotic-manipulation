# Voice-Controlled UR10 Pick and Place System

ROS2 Humble based voice-command robotic manipulation system using UR10 robot and Robotiq 3F gripper.

The system allows controlling robot pick-and-place operations through intelligent command execution, trajectory planning, and gripper control.

---

# Features

- Voice-command robot control
- UR10 pick and place automation
- Robotiq 3F gripper control
- ROS2 Humble support
- Joint trajectory execution
- Real hardware support
- Automatic trajectory topic detection
- Modbus TCP gripper communication
- Object grasp and release control
- Safety-based motion execution
- Robust reconnect logic for gripper
- Real-time robot movement

---

# Hardware Used

- UR10 Robot
- Robotiq 3F Gripper
- Ubuntu 22.04
- ROS2 Humble
- Ethernet LAN Communication

---

# Software Stack

- ROS2 Humble
- Python
- Modbus TCP
- JointTrajectory Controller
- RTDE
- NumPy

---

# System Overview

The robot performs:

1. Move to approach pose
2. Move to pick position
3. Close gripper
4. Lift object
5. Travel to place position
6. Release object

# Robot Motion Sequence

## Pick and Place Poses

```text
P1 → Approach
P2 → Pre-Pick
P3 → Pick
P5 → Lift
P6 → Travel
P7 → Place
```

The robot uses degree-to-radian conversion for accurate UR10 joint control.

---

# Gripper Features

- Object detection feedback
- Automatic reconnect
- Speed and force control
- Basic grasp mode
- Heartbeat communication
- Self-healing connection logic

---

# ROS2 Topics

## Arm Control

```bash
/scaled_joint_trajectory_controller/joint_trajectory
```

## Gripper Control

```bash
/gripper_control
/gripper_pos
```

# Voice Command Examples

Example commands:
- Pick object
- Place object
- Open gripper
- Close gripper
- Start robot
- Stop robot

---

# Safety Features

- Speed-limited trajectory execution
- Teach pendant speed slider support
- Reconnection handling
- Motion timing delays
- Safe trajectory durations

