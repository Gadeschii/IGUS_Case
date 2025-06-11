from .base_robot import BaseRobot
from .utils import wait_until_axes_referenced,check_robot_ready

import time

class RebelLineRobot(BaseRobot):
    def __init__(self, name, **kwargs):
        super().__init__(name=name, **kwargs)
        
def reference_rebelline(self):
    import time
    print("🔧 Referencing REBELLINE: Checking axes...")
    if self.controller.are_all_axes_referenced(axes=("A1", "A2", "A3", "A4", "A5", "A6", "E1")):
        self.move_to_safe_position()
        return

    print("🔧 Referencing E1...")
    time.sleep(0.5)
    if not self.controller.reference_single_joint('E1'):
        raise Exception("❌ Failed to reference E1 in REBELLINE.")

    wait_until_axes_referenced(axes=("E1",), timeout=200)
    print("✅ E1 referenced. Referencing remaining axes...")

    if not self.controller.reference_all_joints():
        raise Exception("❌ Failed to reference remaining joints in REBELLINE.")

    time.sleep(0.2)
    self.wait_until_axes_referenced(axes=("A1", "A2", "A3", "A4", "A5", "A6", "E1"))
    time.sleep(1)
    self.controller.reset()
    time.sleep(0.5)
    self.controller.enable()
    time.sleep(0.5)
    self.move_to_safe_position()
       
        
        
def move_to_safe_position_rebelline(self):
    print("🕹️ Moving RebelLine to safe position...")
    time.sleep(5)

    check_robot_ready(self)

    success = self.controller.move_joints(
        A1=60.0, A2=41.66, A3=51.17, A4=-0.7,
        A5=85.5, A6=-33.5, E1=734.2, E2=0.0, E3=0.0,
        velocity=70.0, acceleration=1.0, wait_move_finished=True
    )
    if not success:
        raise Exception("❌ Failed to move to safe position.")

    print("✅ RebelLine is now safe.")