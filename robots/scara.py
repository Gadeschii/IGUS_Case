from .base_robot import BaseRobot

class ScaraRobot(BaseRobot):
    def __init__(self, name, ip):
        super().__init__(name, ip)