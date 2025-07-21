from enum import Enum
from controllers.logic_controller import LogicController

class SystemState(Enum):
    INIT = 0
    CONNECTING = 1
    REFERENCING = 2
    IMPORTING = 3
    RUNNING = 4
    CLOSING = 5

class StateController:
    def __init__(self, robots):
        self.robots = robots
        self.state = SystemState.INIT
        self.logic = None

    def connect_robots(self):
        print("🔌 Connecting all robots...")
        for robot in self.robots:
            robot.connect()
        self.state = SystemState.CONNECTING
        return "Robots connected"

    def reference_robots(self):
        print("🎯 Referencing all robots...")
        for robot in self.robots:
            robot.reference()
        self.state = SystemState.REFERENCING
        return "Robots referenced"

    def import_variables(self):
        print("📥 Importing variables...")
        for robot in self.robots:
            robot.import_variables()
        self.state = SystemState.IMPORTING
        return "Variables imported"

    def start_logic(self):
        print("🚀 Starting logic controller...")
        self.logic = LogicController(self.robots)
        self.logic.run_scenario()
        self.state = SystemState.RUNNING
        return "Logic sequence started"

    def shutdown(self):
        print("🔒 Shutting down...")
        for robot in self.robots:
            robot.disable()
            robot.close()
        self.state = SystemState.CLOSING
        return "System shut down"
