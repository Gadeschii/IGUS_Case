from robots.scara import ScaraRobot
from robots.rebelline import RebelLineRobot
from robots.rebel1 import Rebel1Robot
from robots.rebel2 import Rebel2Robot
from controllers.state_controller import StateController

def main():
    # 🤖 Initialize robots with their IP addresses
    robots = [
        ScaraRobot("Scara", "192.168.3.10"),
        RebelLineRobot("RebelLine", "192.168.3.11"),
        Rebel1Robot("Rebel1", "192.168.3.12"),
        Rebel2Robot("Rebel2", "192.168.3.13")
    ]
    # 🧠 Start the state controller
    controller = StateController(robots)
    controller.run()

if __name__ == "__main__":
    main()