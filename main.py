from robots.scara import ScaraRobot
from robots.rebelline import RebelLineRobot
from robots.rebel1 import Rebel1Robot
from robots.rebel2 import Rebel2Robot
from controllers.state_controller import StateController
from config.robots_config import robots_config
from robots.base_robot import BaseRobot
from controllers.logic_controller import LogicController
from cri_lib import CRIController
import importlib
import time

def load_robot_class(class_name):
    # module_name = "robots." + class_name.replace("Robot", "").lower()
    module_name = "robots." + class_name.lower() if class_name == "D1Motor" else "robots." + class_name.replace("Robot", "").lower()
    module = importlib.import_module(module_name)
    return getattr(module, class_name)

def main():
    robot_instances = []
    
    for robot_name, config in robots_config.items():
        class_name = config.pop("type")
        robot_class = load_robot_class(class_name)
        
        robot = robot_class(robot_name, **config)
        robot_instances.append(robot)
        print(f"🧱 Createing robot instance: {robot.robot_id} ({robot_class.__name__})")
        time.sleep(0.05)
    print(f"✅ 🧱 Created robot instance")
    print("🔄 Dynamically import robot class from robots.<file>")
    time.sleep(0.25)
        
    print( "\n🔧 Initialize system state controller (connection, reference, import)")
    controller = StateController(robot_instances)
    controller.run_case()


# 🧠 This only runs if you call: python main.py
if __name__ == "__main__":
    main()
    
    
    
    