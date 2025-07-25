from .base_robot import BaseRobot
# from .utils import wait_until_axes_referenced,check_robot_ready

from robots.robot_helpers import wait_until_axes_referenced, check_robot_ready


import time

class RebelLineRobot(BaseRobot):
    def __init__(self, name, **kwargs):
        super().__init__(name=name, **kwargs)
        self.supported_axes = "A1", "A2", "A3", "A4", "A5", "A6", "E1"
        
    def _reference_rebelline(self):
        print("🔧 Referencing REBELLINE: Checking axes...")
        time.sleep(0.1)
        
        if self.controller.are_all_axes_referenced(axes=(self.supported_axes)):
            RebelLineRobot.move_to_safe_position_rebelline(self)
            return
        else:

            print("🔧 Referencing E1...")
            time.sleep(0.5)
            if not self.controller.reference_single_joint('E1'):
                raise Exception("❌ Failed to reference E1 in REBELLINE.")
            
            wait_until_axes_referenced(self,axes=("E1",))
            print("✅ E1 referenced. Referencing remaining axes...")
            
            time.sleep(0.1)
            
            if not self.controller.reference_single_joint('A5'):
                raise Exception("❌ Failed to reference A5 in REBELLINE.")
            
            time.sleep(0.1)
            
            if not self.controller.reference_single_joint('A6'):
                raise Exception("❌ Failed to reference A6 in REBELLINE.")
            
            if not self.controller.reference_all_joints():
                raise Exception("❌ Failed to reference remaining joints in REBELLINE.")

            time.sleep(0.2)
            wait_until_axes_referenced(self,axes=(self.supported_axes))
            time.sleep(0.1)
            self.controller.reset()
            time.sleep(0.5)
            self.controller.enable()
            time.sleep(0.5)
            RebelLineRobot.move_to_safe_position_rebelline(self)
        
    def is_referenced(self):
        try:
            return self.controller.are_all_axes_referenced(self.supported_axes)
        except Exception:
            return False        
            
    def move_to_safe_position_rebelline(self):
        print("🕹️ Moving RebelLine to safe position...")
        time.sleep(0.5)

        check_robot_ready(self)
        print("📋 Checking readiness before safe move:")
        print("🔧 Kinematics ready? = ", self.controller.wait_for_kinematics_ready(timeout=5))
        success = self.controller.move_joints(
            A1=60.0, A2=41.66, A3=51.17, A4=-0.7,
            A5=85.5, A6=-33.5, E1=734.2, E2=0.0, E3=0.0,
            velocity=70.0, acceleration=1.0, wait_move_finished=True
        )
        if not success:
            raise Exception("❌ Failed to move to safe position.")

        print("✅ RebelLine is now safe.")