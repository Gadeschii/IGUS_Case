from cri.controller import CRIController

class BaseRobot:
    def __init__(self, name, ip, port=3920):
        self.name = name
        self.ip = ip
        self.port = port
        self.cri = CRIController()
        self.connected = False

    def connect(self):
        # 🔌 Attempt to connect
        if not self.cri.connect(self.ip, self.port):
            raise RuntimeError(f"❌ Failed to connect with {self.name}.")
        self.connected = True

    def enable(self):
        # ✅ Enable control and motors
        self.cri.set_active_control(True)
        self.cri.enable()

    def reference(self):
        # 🎯 Send reference command to all joints
        self.cri.send_command("ReferenceAllJoints")

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