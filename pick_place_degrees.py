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
POSE_1 = to_rad([92,  -97, 60, -69,  -92, -6])
POSE_2 = to_rad([32,  -70, 34, -84,  -84, 31])
POSE_3 = to_rad([33,  -71, 63, -88,  -86, 31])
POSE_5 = to_rad([33,  -72, 35, -88,  -86, 31])
POSE_6 = to_rad([273, -90, 50, -88,  -86, 31])
POSE_7 = to_rad([273, -77, 110, -121, -94, 13])

class PickPlaceAuto(Node):
    def __init__(self):
        super().__init__('pick_place_auto')
        
        # --- AUTO-DETECT TOPIC ---
        topic_name = self.find_trajectory_topic()
        self.get_logger().info(f'>>> CONNECTED TO: {topic_name} <<<')

        self.arm_pub = self.create_publisher(JointTrajectory, topic_name, 10)

        # Gripper (Fake or Real, doesn't matter for RViz)
        self.gripper_pub = self.create_publisher(Int32MultiArray, '/gripper_control', 10)

        self.get_logger().info('>>> READY <<<')
        input("\nPRESS [ENTER] TO START MOVEMENT...\n")
        self.run_mission()

    def find_trajectory_topic(self):
        """Scans topics to find the correct controller"""
        # We need to wait a moment for ROS to see topics
        time.sleep(1.0) 
        topic_list = self.get_topic_names_and_types()
        
        # Priority 1: Scaled (Real Robot or Realistic Sim)
        for name, types in topic_list:
            if 'scaled_joint_trajectory_controller' in name and 'joint_trajectory' in name and 'state' not in name:
                return name
        
        # Priority 2: Standard (Fake Hardware / Gazebo)
        for name, types in topic_list:
            if 'joint_trajectory_controller' in name and 'joint_trajectory' in name and 'state' not in name:
                return name
                
        self.get_logger().error("COULD NOT FIND TRAJECTORY TOPIC! Is the driver running?")
        # Default fallback
        return '/joint_trajectory_controller/joint_trajectory'

    def run_mission(self):
        self.get_logger().info('--- STARTING ---')

        self.get_logger().info('1. Moving to P1...')
        self.move_arm(POSE_1, duration=4.0)

        self.get_logger().info('2. Moving to P2...')
        self.move_arm(POSE_2, duration=4.0)

        self.get_logger().info('3. Moving to P3 (Pick)...')
        self.move_arm(POSE_3, duration=4.0)

        self.get_logger().info('4. GRASP...')
        time.sleep(1.0)

        self.get_logger().info('5. Lift Up...')
        self.move_arm(POSE_5, duration=4.0)

        self.get_logger().info('6. Traveling...')
        self.move_arm(POSE_6, duration=6.0)

        self.get_logger().info('7. Placing...')
        self.move_arm(POSE_7, duration=4.0)

        self.get_logger().info('8. RELEASE...')
        time.sleep(1.0)

        self.get_logger().info('>>> COMPLETE <<<')

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

def main(args=None):
    rclpy.init(args=args)
    node = PickPlaceAuto()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
