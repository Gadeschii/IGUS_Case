from cri_lib import CRIController
import time

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
        
    def connect(self):
        print(f"\n{'='*30}")
        print(f"🛠️  Prepare robot: {self.robot_id.upper()}")
        print(f"{'='*30}")

        print(f"🔌 Connect to {self.ip}:{self.port}")
        if not self.controller.connect(self.ip, self.port):
            raise Exception("❌ Can't connect to the robot.")

        print("♻️ Reiniciando robot...")
        self.controller.reset()

        print("🔓 Activated remote control...")
        if not self.controller.set_active_control(True):
            raise Exception("❌ Can't activated remote control...")

        print("⚡ Enable robot...")
        if not self.controller.enable():
            raise Exception("❌ Can't Enable robot")

        print("✅ Esperando a que el robot esté listo...")
        if not self.controller.wait_for_kinematics_ready(timeout=30):
            raise Exception("❌ El robot no está listo tras el referenciado.")



    def reference(self):
        # 🎯 Send reference command to all joints
        success = True
        if self.robot_id == "scara":
            print("🔧 Referenciando SCARA: primero A1...")                
            time.sleep(0.5)
            #self.controller.reference_single_joint('A1')
            print(f"📋 Resultado de reference_single_joint('A1'): {success}")
            time.sleep(0.5)
            print("Check referenced axis")
            print(self.controller.are_all_axes_referenced())
            if self.controller.are_all_axes_referenced(axes=("A1", "A2", "A3","A4")):
                self.move_to_safe_position_scara()
            else:

                if not self.controller.reference_single_joint('A1') :
                    raise Exception("❌ Fallo al referenciar A1 en SCARA.")
                
                print("✅ A1 referenciado. Referenciando el resto de ejes...")
                if not self.controller.reference_all_joints():
                    raise Exception("❌ Fallo al referenciar el resto de ejes en SCARA.")
                time.sleep(0.2)

                self.wait_until_axes_referenced(axes=("A1", "A2", "A3", "A4")) 
                time.sleep(1)
                self.controller.reset()
                time.sleep(0.5)
                self.controller.enable()
                time.sleep(0.5)
                self.move_to_safe_position_scara()

        elif self.robot_id == "rebelline":
            if self.controller.are_all_axes_referenced(axes=("A1", "A2", "A3", "A4", "A5", "A6","E1")):

                self.move_to_safe_position_rebelLine()

            else:
                print("🔧 Referenciando REBELLINE: primero E1...")
                time.sleep(0.5)
                # self.controller.reference_single_joint('E1')
                print(f"📋 Resultado de reference_single_joint('E1'): {success}")
                time.sleep(0.5)
                if not self.controller.reference_single_joint('E1'):
                    raise Exception("❌ Fallo al referenciar E1 en REBELLINE.")
                # Esperar a que E1 esté referenciado
                
                self.wait_until_axes_referenced(axes=("E1",), timeout=200)
                print("✅ E1 referenciado. Continuando con el resto de ejes...")

                if not self.controller.reference_all_joints():
                    raise Exception("❌ Fallo al referenciar el resto de ejes en REBELLINE.")

                time.sleep(0.2)

                self.wait_until_axes_referenced(axes=("A1", "A2", "A3", "A4","A5","A6","E1" ))
                time.sleep(1)
                self.controller.reset()
                time.sleep(0.5)
                self.controller.enable()
                time.sleep(0.5)
                self.move_to_safe_position_rebelLine()
                    
        elif self.robot_id == "rebel1":
            print("🎯 Referenciando todos los ejes de..." + self.robot_id)
            if not self.controller.reference_all_joints():
                raise Exception("❌ Fallo al referenciar todos los ejes.")
                
            time.sleep(1)
            self.controller.reset()
            time.sleep(0.5)
            self.controller.enable()
            time.sleep(5)
                
        elif self.robot_id == "rebel2":
            print("🎯 Referenciando todos los ejes de..." + self.robot_id)
            if not self.controller.reference_all_joints():
                raise Exception("❌ Fallo al referenciar todos los ejes.")
            time.sleep(1)
            self.controller.reset()
            time.sleep(0.5)
            self.controller.enable()
            time.sleep(5)
                
        else:
            raise Exception("❌ No identificado " + self.robot_id)

        print("✅ Esperando a que el robot esté listo...")
        if not self.controller.wait_for_kinematics_ready(timeout=30):
            raise Exception("❌ El robot no está listo tras el referenciado.")

        time.sleep(0.5)

    def import_variables(self):
        # 📥 Load required variables (placeholder)
        pass

    def run_task(self):
        # 🚀 Execute main task (placeholder)
        pass

    def disable(self):
        # ⛔ Disable motors
        self.cri.disable()

    def close(self):
        # 🔒 Close CRI connection
        self.cri.close()