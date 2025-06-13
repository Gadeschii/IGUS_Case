from .base_robot import BaseRobot
from .utils import wait_until_axes_referenced, check_robot_ready


import time

class ScaraRobot(BaseRobot):
    def __init__(self, name, **kwargs):
        super().__init__(name=name, **kwargs)
    
    
    def _reference_scara(self):
        print("🔧 Referenciando SCARA: primero A1...")
        time.sleep(0.1)

        if self.controller.are_all_axes_referenced(axes=("A1", "A2", "A3", "A4")):
            ScaraRobot.move_to_safe_position_scara(self)
            return
        else:

            if not self.controller.reference_single_joint('A1'):
                raise Exception("❌ Fallo al referenciar A1 en SCARA.")
            wait_until_axes_referenced(self,axes=("A1",),)
            print("✅ A1 referenciado. Referenciando el resto de ejes...")

            if not self.controller.reference_all_joints():
                raise Exception("❌ Fallo al referenciar el resto de ejes en SCARA.")

            wait_until_axes_referenced(self, ("A1", "A2", "A3", "A4"))
            time.sleep(0.5)
            self.controller.reset()
            time.sleep(0.5)
            self.controller.enable()
            ScaraRobot.move_to_safe_position_scara(self) 
        
    def move_to_safe_position_scara(self):
        print("🕹️ Moving SCARA to safe position...")
        time.sleep(5)

        check_robot_ready(self)

        success = self.controller.move_joints(
            A1=460.0, A2=-74.3, A3=70.0, A4=80.0,
            A5=0.0, A6=0.0, E1=0.0, E2=0.0, E3=0.0,
            velocity=40.0, wait_move_finished=True
        )
        if not success:
            raise Exception("❌ Failed to move to initial safe position.")

        print("⬇️ Position reached. Lowering...")

        successLift = self.controller.move_joints(
            A1=300.0, A2=-74.3, A3=70.0, A4=80.0,
            A5=0.0, A6=0.0, E1=0.0, E2=0.0, E3=0.0,
            velocity=40.0, wait_move_finished=True
        )
        if not successLift:
            raise Exception("❌ Failed to move to final safe position.")

        print("✅ SCARA is now safe.")