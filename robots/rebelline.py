from .base_robot import BaseRobot

class RebelLineRobot(BaseRobot):
    def __init__(self, name, **kwargs):
        super().__init__(name=name, **kwargs)