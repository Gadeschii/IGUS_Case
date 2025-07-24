import time
import importlib
from config.robots_config import robots_config
from robots.base_robot import BaseRobot

from robots.scara import ScaraRobot
from robots.rebelline import RebelLineRobot
from robots.rebel1 import Rebel1Robot
from robots.rebel2 import Rebel2Robot

####################################################################################
#                                  Motor
####################################################################################
def load_robots():
    robots = []

    for config in robots_config.values():
        robot_type = config.get("type")
        class_name = robot_type
        module_name = "robots." + robot_type.lower() if robot_type == "D1Motor" else "robots." + robot_type.replace("Robot", "").lower()

        try:
            module = importlib.import_module(module_name)
            RobotClass = getattr(module, class_name)
        except (ModuleNotFoundError, AttributeError) as e:
            print(f"❌ Could not load class {class_name}: {e}")
            continue

        
        common_args = {
            "name": config.get("id"),
            "program_name": config.get("program_name"),
            "ip": config.get("ip"),
            "sequence_path": config.get("sequence_path"),
            "var_file": config.get("var_file", ""),
            "port": config.get("port"),
            "id": config.get("id")
        }
        
        ###############################################################
        #                   Dryve - D1 Motor
        ###############################################################
     
        if robot_type == "D1Motor":
            common_args["role"] = config.get("role")
            common_args["status"] = config.get("status")
            common_args["shutdown"] = config.get("shutdown")
            common_args["switchOn"] = config.get("switchOn")
            common_args["enableOperation"] = config.get("enableOperation")
            common_args["stop"] = config.get("stop")
            common_args["reset"] = config.get("reset")
            common_args["DInputs"] = config.get("DInputs")

        robot = RobotClass(**common_args)
        robots.append(robot)

    return robots

####################################################################################
#                                  Dryve - D1 Motor
####################################################################################

# def load_robot_class(class_name):
#     module_name = "robots." + class_name.lower() if class_name == "D1Motor" else "robots." + class_name.replace("Robot", "").lower()
#     module = importlib.import_module(module_name)
#     return getattr(module, class_name)

####################################################################################
#                                  Rest of Motor
####################################################################################

# def load_robots():
#     robots = []

#     for config in robots_config.values():
#         robot_type = config.get("type")
#         if robot_type not in ["ScaraRobot", "RebelLineRobot", "Rebel1Robot", "Rebel2Robot"]:
#             continue  
#         common_args = {
#             "name": config.get("id"),
#             "program_name": config.get("program_name"),
#             "ip": config.get("ip"),
#             "sequence_path": config.get("sequence_path"),
#             "var_file": config.get("var_file", ""),
#             "port": config.get("port"),
#             "id": config.get("id")
#         }

#         if robot_type == "ScaraRobot":
#             from robots.scara import ScaraRobot
#             robot = ScaraRobot(**common_args)
#         elif robot_type == "RebelLineRobot":
#             from robots.rebelline import RebelLineRobot
#             robot = RebelLineRobot(**common_args)
#         elif robot_type == "Rebel1Robot":
#             from robots.rebel1 import Rebel1Robot
#             robot = Rebel1Robot(**common_args)
#         elif robot_type == "Rebel2Robot":
#             from robots.rebel2 import Rebel2Robot
#             robot = Rebel2Robot(**common_args)

#         robots.append(robot)

#     return robots

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

   

            