from .base_robot import BaseRobot
import time

class Rebel1Robot(BaseRobot):
    def __init__(self, name, **kwargs):
        super().__init__(name=name, **kwargs)
        
        
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

    