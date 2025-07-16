from cri_lib import CRIController
import time
# from .utils import wait_until_axes_referenced, check_robot_ready
# from .scara import move_to_safe_position_scara

class BaseRobot:
    def __init__(self, name, program_name, ip, sequence_path, var_file, port, id="",remote_folder="Programs", wait_timeout=100):
        self.name = name.capitalize()
        self.program_name = program_name
        self.ip = ip
        self.port = port
        self.sequence_path = sequence_path
        self.remote_folder = remote_folder
        self.wait_timeout = wait_timeout
        self.var_file = var_file
        self.robot_id = id.lower()
        self.controller = CRIController()
        self._last_status = None
        self.connected = False
        
    ####################################################################################
    #                                  E-Stop()
    ####################################################################################
    
    def get_e_stop(self):
        return self.controller.get_e_stop()
        
    ####################################################################################
    #                                  CONNECT()
    ####################################################################################    
    
    def connect(self):
        print(f"\n{'='*30}")
        print(f"🛠️  Preparing robot: {self.robot_id.upper()}")
        print(f"{'='*30}")

        print(f"🔌 Connecting to {self.ip}:{self.port}")
        if not self.controller.connect(self.ip, self.port):
            raise Exception(
            f"❌ Failed to connect to robot '{self.robot_id.upper()}' at {self.ip}:{self.port}.\n"
            f"🔎 Please ensure the robot is powered on and the IP address is correct."
        )

        print("♻️ Restarting robot...")
        self.controller.reset()

        print("🔓 Activating remote control...")
        if not self.controller.set_active_control(True):
            raise Exception("❌ Failed to activate remote control...")

        print("⚡ Enabling robot...")
        if not self.controller.enable():
            raise Exception("❌ Failed to enable robot")

        print("⏳ Waiting for robot to be ready...")
        if not self.controller.wait_for_kinematics_ready(timeout=30):
            raise Exception("❌ Robot not ready after referencing.")
        print(f"✅ {self.robot_id.upper()}: Connected successfully")

    ####################################################################################
    #                               REFERENCE()
    ####################################################################################
    
    def reference(self):
        if self.robot_id == "scara":
            self._reference_scara()
        elif self.robot_id == "rebelline":
            self._reference_rebelline()
        elif self.robot_id in ["rebel1", "rebel2"]:
            self._reference_rebel_generic()
        else:
            raise Exception(f"❌ Unrecognized robot: {self.robot_id}")
        
        print("⏳ Waiting for readiness...")
        if not self.controller.wait_for_kinematics_ready(timeout=30):
            raise Exception("❌ Robot not ready after referencing.")

    def import_variables(self):
        print("📥 Loading required variables...")

        if self.var_file:
            print(f"📤 Uploading variable file: {self.sequence_path + self.var_file}")
            if not self.controller.upload_file(self.sequence_path + self.var_file, self.remote_folder):
                raise Exception("❌ Failed to upload variable file.")
            
            time.sleep(0.1)
            print(f"📦 Loading variable file into memory: {self.var_file}")
            if not self.controller.load_programm(self.var_file):
                raise Exception("❌ Failed to load variable file.")

            print("✅ Variables successfully initialized.")

            print("▶️ Starting variable program...")
            time.sleep(0.5)
            # print("✨ This is where the magic should happen")
            if not self.controller.start_programm():
                raise Exception("❌ Error while starting the variable program.")

            # print(f"🤖 Robot {self.robot_id.upper()} variable state:")
            # print(self.controller.robot_state.variabels)
            # print(f"📍 Robot {self.robot_id} was in the above state")

        print(f"✅ Variable preparation complete for: {self.robot_id.upper()}")
        print(f"\n{'='*30}")

    def run_task(self):
        try:
            print("🚀 Executing main task (placeholder)")
            print(f"\n{'='*30}")
            print(f"▶️  Running sequence for: {self.robot_id.upper()}")
            print(f"{'='*30}")

            print(f"📤 Uploading sequence file: {self.sequence_path + self.program_name}")
            if not self.controller.upload_file(self.sequence_path + self.program_name, self.remote_folder):
                raise Exception("❌ Failed to upload sequence file.")

            print(f"📦 Loading movement program: {self.program_name}")
            if not self.controller.load_programm(self.program_name):
                raise Exception("❌ Failed to load movement program.")

            print(f"▶️ Starting program for {self.robot_id.upper()}")
            if not self.controller.start_programm():
                raise Exception("❌ Error while starting movement program.")
            time.sleep(0.5)

            # self.wait_for_finish_signal()
            # print(f"✅ Sequence completed for: {self.robot_id.upper()}")

        except Exception as e:
            print(f"❌ Error in sequence for {self.robot_id.upper()}: {e}") 

    def disable(self):
        print("⛔ Disabling motors")
        self.controller.disable()

    def close(self):
        print("🔒 Closing CRI connection")
        self.controller.close()
