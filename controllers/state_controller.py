from enum import Enum
from controllers.logic_controller import LogicController

class SystemState(Enum):
    INIT = 0
    CONNECTING = 1
    REFERENCING = 2
    IMPORTING = 3 
    RUNNING = 4
    PAUSED = 5
    CLOSING = 6

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
    
    def reference_robot_by_id(self, robot_id: str):
        for robot in self.robots:
            if robot.robot_id.lower() == robot_id.lower():
                print(f"🎯 Referencing robot: {robot_id}")
                robot.reference()
                return f"Robot '{robot_id}' referenced"
        return f"❌ Robot '{robot_id}' not found"

    def import_variables(self):
        print("📥 Importing variables...")
        for robot in self.robots:
            robot.import_variables()
        self.state = SystemState.IMPORTING
        return "Variables imported"

    def start_logic(self):
        print("🚀 Starting logic controller...")
        self.logic = LogicController(self.robots,  self)
        self.logic.run_scenario()
        self.state = SystemState.RUNNING
        return "Logic sequence started"
    
    def pause_logic(self):
        if self.state == SystemState.RUNNING:
            self.state = SystemState.PAUSED
            print("⏸️ System paused.")
            return "System paused"
        return "Cannot pause. Not currently running."

    def resume_logic(self):
        if self.state == SystemState.PAUSED:
            self.state = SystemState.RUNNING
            print("▶️ Resuming system...")
            return "System resumed"
        return "Cannot resume. System is not paused."

    def shutdown(self):
        print("🔒 Shutting down...")
        for robot in self.robots:
            robot.disable()
            robot.close()
        self.state = SystemState.CLOSING
        return "System shut down"
