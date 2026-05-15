import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Int32MultiArray
from pymodbus.client import ModbusTcpClient
import time

# --- CONFIGURATION ---
GRIPPER_IP = '192.168.1.105'
PORT = 502

class Robotiq3FFinal(Node):
    def __init__(self):
        super().__init__('robotiq_3f_final')
        self.get_logger().info(f'Connecting to {GRIPPER_IP}...')

        # 1. Connect and Keep Open
        self.client = ModbusTcpClient(GRIPPER_IP, port=PORT)
        if not self.client.connect():
            self.get_logger().error("FATAL: Could not connect to gripper!")
            return

        # 2. Activate Gripper
        self.activate_gripper()

        # 3. Heartbeat Timer (Keeps Router Connection Alive)
        self.timer = self.create_timer(2.0, self.heartbeat_callback)

        # 4. Subscribers
        self.create_subscription(String, '/gripper_cmd', self.cmd_callback, 10)
        self.create_subscription(Int32MultiArray, '/gripper_individual', self.individual_callback, 10)
        
        self.get_logger().info('>>> READY! Speed Fixed. Waiting for commands... <<<')

    def activate_gripper(self):
        self.get_logger().info("Resetting (rACT = 0)...")
        try:
            self.client.write_register(0, 0)
            time.sleep(1.0)

            self.get_logger().info("Activating (Waiting 10s)...")
            self.client.write_register(0, 256) # 0x0100
            
            # Keep connection open!
            time.sleep(10.0) 
            self.get_logger().info("Gripper Active.")
        except Exception as e:
            self.get_logger().error(f"Activation Failed: {e}")

    def heartbeat_callback(self):
        """Pings the gripper to prevent Router Timeout"""
        try:
            rr = self.client.read_input_registers(0, 1)
            if rr.isError():
                self.get_logger().warn("Heartbeat lost. Reconnecting...")
                self.client.close()
                self.client.connect()
        except Exception:
            pass

    def cmd_callback(self, msg):
        command = msg.data.lower()
        self.get_logger().info(f"Received: {command}")

        # --- CORRECT MAPPING FOR BASIC MODE (rMOD=0) ---
        # Reg 0: Action (0x0900 -> Act=1, Go=1, Mode=Basic)
        # Reg 1: Position Request (0 = Open, 255 = Close)
        # Reg 2: SPEED & FORCE (65535 = Max Speed, Max Force)
        
        # NOTE: In Basic Mode, Registers 3-7 are ignored by the gripper, 
        # but we keep them at max just to be safe.

        payload = []
        
        if command == 'close':
            payload = [
                2304,   # Reg 0: Activate + Go
                255,    # Reg 1: POS = 255 (Full Close)
                65535,  # Reg 2: SPEED=255, FORCE=255 (Max!)
                65535, 65535, 65535, 65535, 65280 # Ignored in Basic Mode
            ]
        elif command == 'open':
            payload = [
                2304,   # Reg 0: Activate + Go
                0,      # Reg 1: POS = 0 (Full Open)
                65535,  # Reg 2: SPEED=255, FORCE=255 (Max!) <--- THIS WAS 0 BEFORE
                65535, 65535, 65535, 65535, 65280
            ]
        elif command == 'pinch':
             # Pinch requires changing Mode to 2 (0x0D00 -> 3328)
             self.get_logger().info("Pinch Mode...")
             # Reg 0: 3328 (Mode=Pinch)
             # Reg 1: Pos=255 (Close fingers)
             # Reg 2: Speed/Force=Max
             payload = [3328, 255, 65535, 65535, 65535, 65535, 65535, 65280]

        elif command == 'wide':
             # Wide Mode requires changing Mode to 1 (0x0B00 -> 2816)
             self.get_logger().info("Wide Mode...")
             payload = [2816, 0, 65535, 65535, 65535, 65535, 65535, 65280]
            
        else:
            self.get_logger().warn(f"Unknown command: {command}")
            return

        self.send_payload(payload)
        
    def individual_callback(self, msg):
        """Allows setting specific positions: [A, B, C, Scissor]"""
        if len(msg.data) < 4: return
        
        Pa = msg.data[0]
        Pb = msg.data[1]
        Pc = msg.data[2]
        Ps = msg.data[3]
        
        # Pack Registers
        reg0 = 2304
        reg1 = Pa # Pos A
        reg2 = (Pb << 8) | Pc # Pos B | Pos C
        
        # Reg 3: Speed A (255) | Scissor Position
        # If 65280 (0xFF00) worked for Speed, then High Byte is Speed.
        # So Low Byte is Scissor.
        reg3 = (255 << 8) | Ps
        
        payload = [reg0, reg1, reg2, reg3, 65535, 65535, 65535, 65280]
        self.get_logger().info(f"Setting A={Pa} B={Pb} C={Pc} S={Ps}")
        self.send_payload(payload)

    def send_payload(self, payload):
        try:
            result = self.client.write_registers(0, payload)
            if result.isError():
                self.get_logger().error("Modbus Error")
            else:
                self.get_logger().info("Done.")
        except Exception as e:
            self.get_logger().error(f"Write Failed: {e}")
            # Quick reconnect attempt
            try:
                self.client.connect()
                self.client.write_registers(0, payload)
            except:
                pass

def main(args=None):
    rclpy.init(args=args)
    node = Robotiq3FFinal()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
