import time
from config.robots_config import robots_config
from robots.base_robot import BaseRobot

def load_robots():
    robots = []

    for config in robots_config.values():
        if config.get("type") in ["ScaraRobot", "RebelLineRobot", "Rebel1Robot", "Rebel2Robot"]:
            robot = BaseRobot(
                name=config["id"],
                program_name=config.get("program_name"),
                ip=config["ip"],
                sequence_path=config["sequence_path"],
                var_file=config.get("var_file"),
                port=config["port"],
                id=config["id"]
            )
            robots.append(robot)

    return robots

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

##################################################################################### 
#                                      Get Variable() from .xml
#####################################################################################   

def get_variable(self, name: str) -> float:
    """📖 Reads a variable from the robot's state."""
    try:
        return float(self.controller.robot_state.variabels[name])
    except KeyError:
        raise Exception(f"❌ Variable '{name}' not found.")
    
####################################################################################  
  #                                     isFinish + name ()
#################################################################################### 
 
def wait_for_finish_signal(self, signal_base="isfinish"):
    variable_name = f"{signal_base}{self.robot_id}"
    print(f"⏳ Waiting for '{variable_name}' to become 1.0...")

    start = time.time()
    while time.time() - start < self.wait_timeout:
        self.controller.wait_for_status_update(timeout=1)
        time.sleep(0.25)

        try:
            value = float(self.controller.robot_state.variabels[variable_name])
            print(f"🔎 {variable_name} = {value}")
            if value == 1.0:
                print(f"✅ Signal '{variable_name}' detected.")
                return True
        except Exception as e:
            print(f"⚠️ Error reading '{variable_name}': {e}")
        time.sleep(0.5)

    raise TimeoutError(f"❌ Timeout: '{variable_name}' did not become 1.0 in {self.wait_timeout} seconds.")

####################################################################################  
  #                                     General variable
#################################################################################### 

def wait_for_signal(self, var_name: str, expected_value: float = 1.0, timeout=None) -> bool:
    """Waits until a specific variable equals the expected value."""
    timeout = timeout or self.wait_timeout
    print(f"⏳ Waiting for '{var_name}' to become {expected_value}...")

    start = time.time()
    while time.time() - start < timeout:
        self.controller.wait_for_status_update(timeout=1)
        time.sleep(0.25)
        try:
            value = float(self.controller.robot_state.variabels[var_name])
            print(f"🔎 {var_name} = {value}")
            if value == expected_value:
                print(f"✅ '{var_name}' reached expected value.")
                return True
        except Exception as e:
            print(f"⚠️ Error reading '{var_name}': {e}")
        time.sleep(0.5)

    raise TimeoutError(f"❌ Timeout: '{var_name}' did not reach {expected_value} in {timeout} seconds.")

   

            