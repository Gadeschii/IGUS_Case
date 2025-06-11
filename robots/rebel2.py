from .base_robot import BaseRobot

class Rebel2Robot(BaseRobot):
    def __init__(self, name, ip):
        super().__init__(name, ip)