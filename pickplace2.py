import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
import math
import time

# --- HELPER: DEGREES TO RADIANS ---
def to_rad(deg_list):
    return [math.radians(x) for x in deg_list]

# --- POSES (Radians) ---
POSE_1 = to_rad([92,  -97, 60, -69,  -92, -6])   # Approach
POSE_2 = to_rad([32,  -70, 34, -84,  -84, 31])   # Pre-Pick
POSE_3 = to_rad([33,  -71, 63, -88,  -86, 31])   # Pick
POSE_5 = to_rad([33,  -72, 35, -88,  -86, 31])   # Lift
POSE_6 = to_rad([273, -90, 50, -88,  -86, 31])   # Travel (Big Swing)
POSE_7 = to_rad([273, -77, 110, -121, -94, 13])  # Place

class PickPlaceReal(Node):
    def __init__(self):
        super().__init__('pick_place_real')
        
        # --- REAL ROBOT TOPIC ---
        # The 'scaled' controller respects the Teach Pendant speed slider.
        topic_name = '/scaled_joint_trajectory_controller/joint_trajectory'
        
        self.get_logger().info(f'Connecting to REAL ROBOT at: {topic_name}')
        self.arm_pub = self.create_publisher(JointTrajectory, topic_name, 10)

        # Gripper Publisher
        self.gripper_pub = self.create_publisher(Int32MultiArray, '/gripper_control', 10)

        self.get_logger().info('>>> REAL HARDWARE MODE READY <<<')
        self.get_logger().warn('CHECK: Is speed slider at < 30%?')
        input("\nPRESS [ENTER] TO MOVE THE REAL ROBOT...\n")
        self.run_mission()

    def run_mission(self):
        self.get_logger().info('--- STARTING MISSION ---')

        self.get_logger().info('1. Moving to P1 (Approach)...')
        self.move_arm(POSE_1, duration=6.0)

        self.get_logger().info('2. Moving to P2 (Pre-Pick)...')
        self.move_arm(POSE_2, duration=5.0)

        self.get_logger().info('3. Moving to P3 (Pick)...')
        self.move_arm(POSE_3, duration=4.0)

        self.get_logger().info('4. GRASPING OBJECT...')
        # Pos=255, Speed=150, Force=20 (Soft Grip)
        self.control_gripper(255, 150, 20) 
        time.sleep(3.0) 

        self.get_logger().info('5. Lifting Up (P5)...')
        self.move_arm(POSE_5, duration=4.0)

        self.get_logger().info('6. Traveling to Place Side (P6)...')
        # Long duration for safety on the big swing
        self.move_arm(POSE_6, duration=8.0) 

        self.get_logger().info('7. Placing (P7)...')
        self.move_arm(POSE_7, duration=5.0)

        self.get_logger().info('8. RELEASING OBJECT...')
        self.control_gripper(0, 150, 20)
        time.sleep(2.0)

        self.get_logger().info('>>> MISSION COMPLETE <<<')

    def move_arm(self, joint_positions, duration=5.0):
        msg = JointTrajectory()
        msg.joint_names = [
            'shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
            'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint'
        ]
        point = JointTrajectoryPoint()
        point.positions = joint_positions
        point.time_from_start = Duration(sec=int(duration), nanosec=0)
        msg.points.append(point)
        
        self.arm_pub.publish(msg)
        time.sleep(duration + 0.5)

    def control_gripper(self, pos, speed, force):
        msg = Int32MultiArray()
        msg.data = [pos, speed, force]
        self.gripper_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = PickPlaceReal()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
