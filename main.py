from robots.scara import ScaraRobot
from robots.rebelline import RebelLineRobot
from robots.rebel1 import Rebel1Robot
from robots.rebel2 import Rebel2Robot
from controllers.state_controller import StateController
from config.robots_config import robots_config
from robots.base_robot import BaseRobot
import importlib

def load_robot_class(class_name):
    """🔄 Import class dynamically from robots.<file>"""
    module_name = "robots." + class_name.replace("Robot", "").lower()
    module = importlib.import_module(module_name)
    return getattr(module, class_name)

def main():
    robot_instances = []

    for robot_name, config in robots_config.items():
        class_name = config.pop("type")
        robot_class = load_robot_class(class_name)
        robot = robot_class(robot_name, **config)
        robot_instances.append(robot)

    controller = StateController(robot_instances)
    controller.run()

# 🧠 This only runs if you call: python main.py
if __name__ == "__main__":
    main()
    
    
    
    