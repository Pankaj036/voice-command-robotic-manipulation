import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
from pymodbus.client import ModbusTcpClient
import time

# --- CONFIGURATION ---
GRIPPER_IP = '192.168.1.105'
PORT = 502

class Robotiq3FRobust(Node):
    def __init__(self):
        super().__init__('robotiq_3f_robust')
        self.get_logger().info(f'Connecting to {GRIPPER_IP}...')

        # 1. Setup Client (But don't panic if it fails yet)
        self.client = ModbusTcpClient(GRIPPER_IP, port=PORT)
        
        # 2. Activate Gripper
        if self.connect_and_activate():
            self.get_logger().info('>>> SYSTEM READY <<<')
            self.get_logger().info('Command Topic: /gripper_pos (0-255)')
        else:
            self.get_logger().error('Initial Connection Failed. Will retry on first command.')

        # 3. Heartbeat (Background Keep-Alive)
        self.timer = self.create_timer(2.0, self.heartbeat_callback)

        # 4. Subscriber
        self.create_subscription(Int32, '/gripper_pos', self.pos_callback, 10)

    def connect_and_activate(self):
        """Connects and sends the Activation Request"""
        try:
            self.client.connect()
            # Reset
            self.client.write_register(0, 0)
            time.sleep(0.5)
            # Activate
            self.client.write_register(0, 256) # 0x0100
            # Wait for calibration
            time.sleep(2.0) 
            return True
        except Exception as e:
            self.get_logger().error(f"Activation Error: {e}")
            return False

    def heartbeat_callback(self):
        """Pings the gripper to keep the router happy"""
        try:
            # Just read status to keep traffic flowing
            self.client.read_input_registers(0, 1)
        except:
            # If heartbeat fails, we don't panic. 
            # We let the 'send_command' function handle the reconnection later.
            pass

    def pos_callback(self, msg):
        """Handles the incoming command with AUTO-RECONNECT logic"""
        target_pos = max(0, min(255, msg.data))
        self.get_logger().info(f"Target: {target_pos}/255")

        # Basic Mode Payload:
        # Reg 0: 0x0900 (Act=1, Go=1, Mode=Basic) -> 2304
        # Reg 1: Position (0-255)
        # Reg 2: Speed & Force (Max) -> 65535
        payload = [
            2304,       
            target_pos, 
            65535,      
            65535, 65535, 65535, 65535, 65280
        ]

        # --- THE SELF-HEALING SEND BLOCK ---
        success = False
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Try to write
                result = self.client.write_registers(0, payload)
                
                if result.isError():
                    # If Modbus logic error, raise exception to trigger reconnect
                    raise Exception("Modbus Logic Error")
                
                # If we get here, it worked!
                self.get_logger().info("Move Success.")
                success = True
                break 

            except Exception as e:
                # If "Broken Pipe" or connection lost:
                self.get_logger().warn(f"Connection lost ({e}). Reconnecting...")
                
                # Force close and Re-open
                self.client.close()
                time.sleep(0.2) # Short breath
                self.client.connect()
                
                # Loop will now try sending again...

        if not success:
            self.get_logger().error("FAILED to move gripper after 3 retries.")

def main(args=None):
    rclpy.init(args=args)
    node = Robotiq3FRobust()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
