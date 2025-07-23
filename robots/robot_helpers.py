import time

def wait_until_axes_referenced(self, axes=("A1", "A2", "A3", "A4", "A5", "A6", "E1"), timeout = 400) -> bool:
    print(f"⏳ Waiting for axes {axes} to be referenced...")
    start = time.time()
    while time.time() - start < timeout:
        if self.controller.are_all_axes_referenced(axes):
            print("♻️ Second reset...")
            self.controller.reset()

            print("🔓 Enabling remote control...")
            if not self.controller.set_active_control(True):
                raise Exception("❌ Could not enable remote control.")

            print("⚡ Enabling robot...")
            if not self.controller.enable():
                raise Exception("❌ Could not enable the robot.")

            return True
        time.sleep(1)
    raise TimeoutError(f"❌ Timeout: Axes {axes} not referenced in time.")

  ####################################################################################  
  #                                      CHECK()
   ####################################################################################   
def check_robot_ready(self):
    if not self.controller.robot_state.active_control:
        raise Exception("❌ Remote control is not active.")

    if not self.controller.robot_state.main_relay:
        raise Exception("❌ Main relay is not active.")

    for i, err in enumerate(self.controller.robot_state.error_states):
        if any([getattr(err, attr) for attr in vars(err)]):
            raise Exception(f"❌ Error on axis {i}: {err}")
    print("✅ Safe SCARA position.")