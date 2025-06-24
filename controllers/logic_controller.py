from cri_lib import CRIController
import time
import random
import threading
import time
from controllers.color_detector import *
from dotenv import load_dotenv
from controllers.usb_pingpong_detector import usb_detect_pingpong_color
import os

load_dotenv()
RTSP_URL = os.getenv("RTSP_URL")
RTSP_URL_2 = os.getenv("RTSP_URL_2")

DOOR_CLOSED_POS = 0.0
DOOR_OPEN_POS = 100.0 # tengo qeu mirar para que el open door sea dar una vuelta

ELEVATOR_BOTTOM_POS = 0.0
ELEVATOR_TOP_POS = 250.0

class LogicController:
    def __init__(self, robots):
        self.robots = robots
        self.robot_map = {robot.robot_id: robot for robot in robots}
        self._was_in_emergency = False
        self.d1_door = None
        self.d1_elevator = None

        for robot in robots:
            if robot.__class__.__name__ == "D1Motor":
                if getattr(robot, "role", None) == "door":
                    self.d1_door = robot
                elif getattr(robot, "role", None) == "elevator":
                    self.d1_elevator = robot

    def get_robot_vars(self, robot_name):
        return self.robot_map[robot_name.lower()].controller.robot_state.variabels

    def check_emergency_by_motor_status(self):
        for robot_id, robot in self.robot_map.items():
            # Saltar los D1Motor que no tienen controlador CRI
            if not hasattr(robot, "controller"):
                continue
            if not robot.controller.motors_are_enabled():
                print(f"🛑 Detected disabled motors on {robot_id.upper()} → possible E-STOP")
                return True
        return False


    def print_robot_variables_periodically(self):
        while True:
            try:
                for name in ["Scara", "RebelLine", "Rebel1", "Rebel2"]:
                    vars_ = self.get_robot_vars(name)
                    print(f"🔍 {name} variables:  {vars_}\n{'--'*30}")

                if self.d1_door:
                    print(f"🚪 D1 Door position: {self.d1_door.current_position}")
                if self.d1_elevator:
                    print(f"🏗️ D1 Elevator position: {self.d1_elevator.current_position}")
                print(f"{'='*60}")

            except Exception as e:
                print(f"⚠️ Error while printing robot variables: {e}")
            time.sleep(15)

    def run_scenario(self):
        print("\n🔁 Starting infinite production loop, waiting for objet")

        isObjForScara = False
        isObjForRebelLine = False

        # threading.Thread(target=self.print_robot_variables_periodically, daemon=True).start()

        while True:

            # =========================
            # 🛑 Check for emergency stop
            # =========================
            in_emergency = self.check_emergency_by_motor_status()

            if in_emergency:
                if not self._was_in_emergency:
                    print("🚨 Emergency state detected by motor status.")
                print("🕒 Waiting for all emergency stops to be released...")
                time.sleep(2)
                self._was_in_emergency = True


                continue

            elif self._was_in_emergency:
                # Solo entra aquí cuando se ha recuperado del estado de emergencia
                print("✅ Emergency stop cleared! Restarting sequence...")
                for robot_id, robot in self.robot_map.items():
                    print(f"♻️ Re-importing variables for {robot_id.upper()}")
                    robot.import_variables()
                self._was_in_emergency = False

            try:
                scara_vars = self.get_robot_vars("Scara")
                rebelline_vars = self.get_robot_vars("RebelLine")
                rebel1_vars = self.get_robot_vars("Rebel1")
                rebel2_vars = self.get_robot_vars("Rebel2")


                #=====================================================
                #               🤖 Dry D1 robot logic
                #=====================================================

                if self.d1_door:
                    # Ensure motor is referenced before any movement
                    self.d1_door.reference()

                    if not isObjForScara and not isObjForRebelLine:
                        try:
                            # Try to detect the ping pong ball
                            ball_detected = False
                            try:
                                whiteBall = detect_pingpong_presence_color_white(RTSP_URL)
                                blueBall = detect_pingpong_presence_color_blue(RTSP_URL)
                                ball_detected = whiteBall or blueBall
                            except RuntimeError as e:
                                print(f"⚠️ Ping pong detection error: {e}")

                            if ball_detected:
                                print("✅ Ping pong ball detected → SCARA task ready")
                                isObjForScara = True

                                # 🔒 Move door to closed position
                                self.d1_door.move_to_closed()
                                self.d1_door.current_position = 0.0

                            else:
                                raise RuntimeError("❌ No ping pong ball detected.")

                        except RuntimeError as e:
                            print(f"⚠️ {e}")
                            # 🚪 Open the door
                            self.d1_door.move_to_open()
                            self.d1_door.current_position = 250.0  # mm (or appropriate open value)


                if self.d1_elevator:
                    if rebelline_vars.get("startascensor", 0.0) == 1.0:
                        self.d1_elevator.move_to(ELEVATOR_TOP_POS)
                        time.sleep(0.5)
                        self.d1_elevator.move_to(ELEVATOR_BOTTOM_POS)

                print('========================================================')
                print(f"Is there object for Rebel Line? --> {isObjForRebelLine} ")
                print(f"Is there object for Scara? --> {isObjForScara} ")
                print('========================================================')

                #=====================================================
                #               🤖 SCARA robot logic
                #=====================================================
                if(
                    isObjForScara and
                    not detect_pingpong_presence_color_white2(RTSP_URL_2) and
                    not detect_pingpong_presence_color_blue2(RTSP_URL_2) and
                    scara_vars.get("startscara", 0.0) == 0.0
                ):
                    print("🟢 Starting initial SCARA task...")
                    self.robot_map["scara"].run_task()
                    isObjForScara = False

                #=====================================================
                #          🔄 SCARA triggers REBELLINE flag
                #=====================================================
                if True: #scara_vars.get("posdropobjscara") == 1.0:
                    # test
                    #isObjForRebelLine = True
                    try:
                        ball_detected2 = False
                        # 🔍 Check presence of ball using RL camera
                        whiteBall2 = detect_pingpong_presence_color_white2(RTSP_URL_2)
                        blueBall2 = detect_pingpong_presence_color_blue2(RTSP_URL_2)
                        ball_detected2 = whiteBall2 or blueBall2
                        
                        print("ENTREACA==================================================")
                        print(f"Ball detected: {ball_detected2}")
                        print("SALIACA==================================================")
                        
                        if ball_detected2:
                            isObjForRebelLine = True
                            print("🎥 RL camera confirmed object → isObjForRebelLine = True")
                        else:
                            print("⚠️ RL camera did NOT detect object → skipping.")
                    except Exception as e:
                        print(f"❌ USB camera error: {e}")

                    print("📦 SCARA dropped object → there is objet for Rebel Line")

                if rebelline_vars.get("posreciverebelline1") == 1.0 or rebelline_vars.get("posreciverebelline2") == 1.0 :
                    isObjForRebelLine = detect_pingpong_presence_color_white2(RTSP_URL_2) and detect_pingpong_presence_color_blue2(RTSP_URL_2) #False
                    print("🔄 RebelLine received object → there isn't objet for Rebel Line")

                 #---------------Reset SCARA variable---------------------

                if scara_vars.get("isfinishscara", 0.0) == 1.0:
                    print("\n♻️ Resetting SCARA variables...")
                    self.robot_map["scara"].import_variables()
                    # 🔄 Recargar variables después de importarlas
                    scara_vars = self.get_robot_vars("Scara")

                #=====================================================
                #              🤖 REBELLINE robot logic
                #=====================================================
                print (f"Rebel Line Camara white {detect_pingpong_presence_color_white2(RTSP_URL_2)}")
                print (f"Rebel Line Camara blue {detect_pingpong_presence_color_blue2(RTSP_URL_2)}")
                if (
                     isObjForRebelLine and
                    # (detect_pingpong_presence_color_white2(RTSP_URL_2) or detect_pingpong_presence_color_blue2(RTSP_URL_2)) and
                    rebelline_vars.get("startrebelline") == 0.0 #and (
                    #     scara_vars.get("startscara") == 1.0 or
                    #     scara_vars.get("isfinishscara") == 0.0
                    # )
                ):
                    print("📦 Detected object dropped by SCARA → REBELLINE")
                    
                    print(f"Rebel variables: {rebelline_vars}")

                    try:
                        whiteBall3 = detect_pingpong_presence_color_white2(RTSP_URL_2)
                        blueBall3 = detect_pingpong_presence_color_blue2(RTSP_URL_2)
                        if whiteBall3:
                            color = "white"
                        elif blueBall3:
                            color = "blue"
                        #color = detect_pingpong_presence(RTSP_URL, show_debug=True)
                        print(f"🎨 Detected color: {color}")

                        if color == "white":
                            print("🎲 Color is WHITE → Load RebelLine1 sequence")
                            self.robot_map["rebelline"].program_name = "RebelLine1.xml"
                            rebelline_vars["lastprogram"] = "RebelLine1"
                        elif color in ("black", "blue"):
                            print(f"🎲 Color is {color.upper()} → Load RebelLine2 sequence")
                            self.robot_map["rebelline"].program_name = "RebelLine2.xml"
                            rebelline_vars["lastprogram"] = "RebelLine2"
                        else:
                            raise ValueError(f"❌ Unknown color detected: {color}")

                        self.robot_map["rebelline"].sequence_path = "sequences/RebelLine/"
                        self.robot_map["rebelline"].run_task()
                        rebelline_vars["startrebelline"] = 1.0

                    except RuntimeError as e:
                        print(f"⚠️ Camera error: {e}")
                    except Exception as e:
                        print(f"⚠️ Color detection failed: {e}")

                #---------------Reset Rebel Line variable---------------------
                if (
                    rebelline_vars.get("isfinishrebelline1", 0.0) == 1.0 or
                    rebelline_vars.get("isfinishrebelline2", 0.0) == 1.0
                ):
                    print("\n♻️ Resetting Rebel Line variables...")
                    self.robot_map["rebelline"].import_variables()
                    # 🔄 Recargar variables después de importarlas
                    rebelline_vars = self.get_robot_vars("RebelLine")

                #=====================================================
                #                   🤖 REBEL1 robot logic
                #=====================================================
                print("\n🔍 REVISIÓN PARA REBEL1")
                print(f"posdropobjrebellinetorebel1 = {rebelline_vars.get('posdropobjrebellinetorebel1')}")
                print(f"startrebel1 = {rebel1_vars.get('startrebel1')}")
                print(f"isfinishrebelline1 = {rebelline_vars.get('isfinishrebelline1')}")
                print(f"lastprogram = {rebelline_vars.get('lastprogram')}")
                
                if (
                    rebelline_vars.get("posdropobjrebellinetorebel1") == 1.0 and
                    # rebelline_vars.get("lastprogram") == "RebelLine1" and
                    rebel1_vars.get("startrebel1") == 0.0
                ):
                    print("📦 REBELLINE dropped to REBEL1")
                    self.robot_map["rebel1"].run_task()
                    rebel1_vars["startrebel1"] = 1.0

                if rebel1_vars.get("isfinishrebel1", 0.0) == 1.0:
                    print("\n♻️ Resetting REBEL1 variables...")
                    self.robot_map["rebel1"].import_variables()
                    rebel1_vars = self.get_robot_vars("Rebel1")

                #=====================================================
                #                  🤖 REBEL2 robot logic
                #=====================================================
                
                print("\n🔍 REVISIÓN PARA REBEL2")
                print(f"posdropobjrebellinetorebel2 = {rebelline_vars.get('posdropobjrebellinetorebel2')}")
                print(f"startrebel2 = {rebel1_vars.get('startrebel2')}")
                print(f"isfinishrebelline1 = {rebelline_vars.get('isfinishrebelline2')}")
                print(f"lastprogram = {rebelline_vars.get('lastprogram')}")
                if (
                    rebelline_vars.get("posdropobjrebellinetorebel2") == 1.0 and
                    # rebelline_vars.get("lastprogram") == "RebelLine2" and
                    rebel2_vars.get("startrebel2") == 0.0
                ):
                    print("📦 REBELLINE dropped to REBEL2")
                    self.robot_map["rebel2"].run_task()
                    rebel2_vars["startrebel2"] = 1.0

                if rebel2_vars.get("isfinishrebel2", 0.0) == 1.0:
                    print("\n♻️ Resetting REBEL2 variables...")
                    self.robot_map["rebel2"].import_variables()
                    rebel2_vars = self.get_robot_vars("Rebel2")
                time.sleep(1)

            except Exception as e:
                print(f"⚠️ Logic loop error: {e}")
                time.sleep(1)

