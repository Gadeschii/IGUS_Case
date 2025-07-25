from .base_robot import BaseRobot
import time

class Rebel1Robot(BaseRobot):
    def __init__(self, name, **kwargs):
        super().__init__(name=name, **kwargs)
        self.supported_axes = ("A1", "A2", "A3", "A4", "A5", "A6")


        
        
    def _reference_rebel_generic(self):
       
        print(f"🎯 Referencing all joints of {self.robot_id.upper()}...")
        if not self.controller.reference_all_joints():
            raise Exception("❌ Failed to reference all joints.")
        print(f"{self.robot_id.upper()}, referenced")
        

        time.sleep(0.1)
        self.controller.reset()
        time.sleep(0.5)
        self.controller.enable()
        time.sleep(0.5)

    def is_referenced(self):
        try:
            return self.controller.are_all_axes_referenced(self.supported_axes)
        except Exception:
            return False