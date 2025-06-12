import time
import random

class LogicController:
    def __init__(self, robots):
        self.robots = robots
        self.robot_map = {robot.robot_id: robot for robot in robots}

    def get_robot_vars(self, robot_name):
        return self.robot_map[robot_name.lower()].controller.robot_state.variabels
    
    def get_e_stop(self):
        """Return True if emergency stop is pressed, False otherwise."""
        try:
            result = self.send_and_receive("get estop")
            return result.strip() == "1"
        except Exception as e:
            print(f"⚠️ Error checking e-stop: {e}")
            return False
        
    def check_emergency_stops(self):
        for robot_id, robot in self.robot_map.items():
            if robot.controller.get_e_stop():
                print(f"🛑 Emergency stop detected on robot: {robot_id.upper()}")
        
    def run_scenario(self):
        print("\n🔁 Starting infinite production loop...")
        while True:
            try:
                scara_vars = self.get_robot_vars("Scara")
                rebelline_vars = self.get_robot_vars("RebelLine")
                rebel1_vars = self.get_robot_vars("Rebel1")
                rebel2_vars = self.get_robot_vars("Rebel2")

                print(f"🔍 Scara variables:  {scara_vars}")
                print(f"\n{'--'*30}")
                print(f"🔍 Rebel Line variables:  {rebelline_vars}")
                print(f"\n{'--'*30}")

                #=====================================================
                #               🤖 SCARA robot logic
                #=====================================================
                if scara_vars.get("startscara", 0.0) == 0.0:
                    print("🟢 Starting initial SCARA task...")
                    self.robot_map["scara"].run_task()

                #=====================================================
                #              🤖 REBELLINE robot logic
                #=====================================================
                if (
                    scara_vars.get("posdropobjscara") == 1.0 and
                    rebelline_vars.get("startrebelline") == 0.0 and
                    scara_vars.get("startscara") == 1.0
                ):
                    print("📦 Detected object dropped by SCARA → REBELLINE")
                    print(f"Rebel variables: {rebelline_vars}")

                    obj_type = random.randint(1, 100)

                    if obj_type % 2 == 0:
                        print("🎲 Object type is EVEN → Load RebelLine2 sequence")
                        self.robot_map["rebelline"].program_name = "RebelLine2.xml"
                        rebelline_vars["lastprogram"] = "RebelLine2"
                    else:
                        print("🎲 Object type is ODD → Load RebelLine1 sequence")
                        self.robot_map["rebelline"].program_name = "RebelLine1.xml"
                        rebelline_vars["lastprogram"] = "RebelLine1"

                    self.robot_map["rebelline"].sequence_path = "sequences/RebelLine/"
                    self.robot_map["rebelline"].run_task()

                #=====================================================
                #                   🤖 REBEL1 robot logic
                #=====================================================
                if (
                    rebelline_vars.get("posdropobjrebellinetorebel1") == 1.0 and
                    rebelline_vars.get("lastprogram") == "RebelLine1" and
                    rebel1_vars.get("startrebel1") == 0.0
                ):
                    print("📦 REBELLINE dropped to REBEL1")
                    self.robot_map["rebel1"].run_task()
                    rebel1_vars["startrebel1"] = 1.0

                #=====================================================
                #                  🤖 REBEL2 robot logic
                #=====================================================
                if (
                    rebelline_vars.get("posdropobjrebellinetorebel2") == 1.0 and
                    rebelline_vars.get("lastprogram") == "RebelLine2" and
                    rebel2_vars.get("startrebel2") == 0.0
                ):
                    print("📦 REBELLINE dropped to REBEL2")
                    self.robot_map["rebel2"].run_task()
                    rebel2_vars["startrebel2"] = 1.0

                time.sleep(1)

            except Exception as e:
                print(f"⚠️ Logic loop error: {e}")
                time.sleep(1)
