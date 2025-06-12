from enum import Enum
import time
from controllers.logic_controller import LogicController

class SystemState(Enum):
    CONNECTING = 1
    REFERENCING = 2
    IMPORTING = 3
    RUNNING = 4
    CLOSING = 5

class StateController:
    def __init__(self, robots):
        self.robots = robots
        self.state = SystemState.CONNECTING

    def run_case(self):
        while self.state != SystemState.CLOSING:
            if self.state == SystemState.CONNECTING:
                print("\n" + "*" * 30)
                print("🔌 Connecting all robots...")
                for robot in self.robots:
                    robot.connect()
                self.state = SystemState.REFERENCING

            elif self.state == SystemState.REFERENCING:
                print("\n" + "*" * 30)
                print("🎯 Referencing all robots...")
                for robot in self.robots:
                    robot.reference()
                self.state = SystemState.IMPORTING

            elif self.state == SystemState.IMPORTING:
                print("\n" + "*" * 30)
                print("📥 Importing variables...")
                for robot in self.robots:
                    robot.import_variables()
                self.state = SystemState.RUNNING

            elif self.state == SystemState.RUNNING:
                print("\n" + "*" * 30)
                print("🚀 Initial startup complete, passing control to logic controller...")     
                logic = LogicController(self.robots)
                print("\n🧠 Start coordination logic between robots")
                logic.run_scenario()  # Esto es un bucle infinito, así que no saldrá de aquí a menos que falle

                break 

        print("\n" + "*" * 30)
        print("🔒 Closing all robot sessions...")
        for robot in self.robots:
            robot.disable()
            robot.close()