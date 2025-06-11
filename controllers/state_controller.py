from enum import Enum

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

    def run(self):
        while self.state != SystemState.CLOSING:
            if self.state == SystemState.CONNECTING:
                print(f"\n{'*'*30}")
                print ("🔌 Connecting all robots...") 
                print(f"\n{'*'*30}")
                for robot in self.robots:
                    robot.connect()
                self.state = SystemState.REFERENCING

            elif self.state == SystemState.REFERENCING:
                print(f"\n{'*'*30}")
                print ("🎯 Referencing all robots...") 
                print(f"\n{'*'*30}")
                for robot in self.robots:
                    robot.reference()
                self.state = SystemState.IMPORTING

            elif self.state == SystemState.IMPORTING:
                print(f"\n{'*'*30}")
                print ("📥 Importing variables...") 
                print(f"\n{'*'*30}")
                for robot in self.robots:
                    robot.import_variables()
                self.state = SystemState.RUNNING

            elif self.state == SystemState.RUNNING:
                print(f"\n{'*'*30}")
                print ("🚀 Running tasks...")  
                print(f"\n{'*'*30}")
                for robot in self.robots:
                    robot.run_task()
                self.state = SystemState.CLOSING

        print(f"\n{'*'*30}")
        print ("🔒 Closing all robot sessions...") 
        print(f"\n{'*'*30}")
        for robot in self.robots:
            robot.disable()
            robot.close()