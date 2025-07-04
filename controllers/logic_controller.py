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

class LogicController:
    def __init__(self, robots):
        self.robots = robots
        self.robot_map = {robot.robot_id: robot for robot in robots}
        self._was_in_emergency = False
        self.d1_door = None
        self.d1_elevator = None
        self.RebelLineStart = False
        self.ScaraStarted = False
        
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

                # if self.d1_door:
                #     print(f"🚪 D1 Door position: {self.d1_door.current_position}")
                # if self.d1_elevator:
                #     print(f"🏗️ D1 Elevator position: {self.d1_elevator.current_position}")
                # print(f"{'='*60}")

            except Exception as e:
                print(f"⚠️ Error while printing robot variables: {e}")
            time.sleep(5)

    def run_scenario(self):
        print("\n🔁 Starting infinite production loop, waiting for objet")

        isObjForScara = False
        isObjForRebelLine = False

        threading.Thread(target=self.print_robot_variables_periodically, daemon=True).start()

        while True:

            # =========================
            # 🛑 Check for emergency stop
            # =========================
            
            # 🚨 Emergency check (stop everything and disconnect)
            if self.check_emergency_by_motor_status():
                print("\n🛑 Emergency detected — stopping all operations and disconnecting all robots")
                for robot in self.robots:
                    try:
                        robot.disable()
                        robot.close()
                        print(f"🔌 {robot.robot_id.upper()} disconnected successfully.")
                    except Exception as e:
                        print(f"⚠️ Failed to disconnect {robot.robot_id.upper()}: {e}")
                break  # ⛔ Exit infinite loop
            try:
                scara_vars = self.get_robot_vars("Scara")
                rebelline_vars = self.get_robot_vars("RebelLine")
                rebel1_vars = self.get_robot_vars("Rebel1")
                rebel2_vars = self.get_robot_vars("Rebel2")
                
                print('========================================================')
                print(f"Is there object for Rebel Line? --> {isObjForRebelLine} ")
                print(f"Is there object for Scara? --> {isObjForScara} ")
                print('========================================================')

                #=====================================================
                #               🤖 Dry D1 robot logic
                #=====================================================
                if self.d1_door:
                    self.d1_door.reference()
                    
                    # Scara camera
                    detected_scara, color_scara = detect_ball_and_color(RTSP_URL)
                    
                    print(f"🎥 [SCARA CAM] Ball detected? → isObjForScara = {isObjForScara}")
                    print(f"🔎 [SCARA CAM] Raw detection result (detected_scara) → {detected_scara}")
                    print(f"🎨 [SCARA CAM] Detected ball color → {color_scara} (It's not necessary)")
                    print("📦 Ball ready for SCARA → SCARA can start its task")

                    # ========== 🎯 SCARA ball detection ==========
                    if not isObjForScara:
                        try:
                            detected_scara, _ = detect_ball_and_color(RTSP_URL)
                            if detected_scara:
                                print("✅ Ping pong ball detected → SCARA task ready")
                                isObjForScara = True
                                # 🔒 Move door to closed position
                                self.d1_door.move_to_left() 
                                # self.d1_door.current_position = 0.0
                            else:
                                print("⏳ No ball yet for SCARA")
                                # 🚪 Open the door
                                self.d1_door.move_to_right() 
                                # self.d1_door.current_position = -250.0  
                        except RuntimeError as e:
                            print(f"⚠️ SCARA camera error: {e}")

                #=====================================================
                #               🤖 SCARA robot logic
                #=====================================================      
                                
                if (
                    isObjForScara and
                    not detect_ball_and_color(RTSP_URL_2)[0] and
                    scara_vars.get("startscara") == 0.0
                ):
                    print("🟢 Starting initial SCARA task...")
                    self.robot_map["scara"].run_task()
                    isObjForScara = False
                    

                #=====================================================
                #          🔄 SCARA triggers REBELLINE flag
                #=====================================================
                
                # RebelLine camera
                detected_rebel, color_rebel = detect_ball_and_color(RTSP_URL_2)
                if detected_rebel:
                    isObjForRebelLine = True
                    print(f"🎥 [REBEL CAM] Ball detected? → isObjForRebelLine = {isObjForRebelLine}")
                    print(f"🔎 [REBEL CAM] Raw detection result (detected_rebel) → {detected_rebel}")
                    print(f"🎨 [REBEL CAM] Detected ball color → {color_rebel} ")
                    print("📦 SCARA dropped object → there is object for Rebel Line")
                    
                else:
                    print("⚠️ RL camera did NOT detect object → skipping.")


                if rebelline_vars.get("posreciverebelline1") == 1.0 or rebelline_vars.get("posreciverebelline2") == 1.0:
                    isObjForRebelLine = False     
                    #isObjForRebelLine = detect_pingpong_presence_color_white2(RTSP_URL_2) and detect_pingpong_presence_color_blue2(RTSP_URL_2) #False
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
                # 1. Detectar presencia y color desde cámara RTSP_URL_2
                try:
                    print(f"🎥 Rebel camera detected: {detected_rebel}, color: {color_rebel}")
                except Exception as e:
                    detected_rebel, color_rebel = False, None
                    print(f"⚠️ Rebel camera detection error: {e}")

                # 2. Guardar flag de objeto para RebelLine
                isObjForRebelLine = detected_rebel
                
                # 3. Lógica de ejecución si hay objeto y condiciones de SCARA son válidas
                if (
                    isObjForRebelLine and 
                    rebelline_vars.get("startrebelline1") == 0.0 and
                    rebelline_vars.get("startrebelline2") == 0.0  and 
                    (
                        scara_vars.get("posdropobjscara") == 1.0 or
                        scara_vars.get("startscara") == 0.0 or
                        scara_vars.get("isfinishscara") == 1.0
                    )
                ):
                    print("📦 Detected object dropped by SCARA → REBELLINE")

                    try:
                        if color_rebel == "white" or color_rebel == "orange":
                            self.robot_map["rebelline"].program_name = "RebelLine1.xml"
                            rebelline_vars["lastprogram"] = "RebelLine1"
                            print(f"🤖 Load: RebelLine1")
                        elif color_rebel == "blue":
                            self.robot_map["rebelline"].program_name = "RebelLine2.xml"
                            rebelline_vars["lastprogram"] = "RebelLine2"
                            print(f"🤖 Load: RebelLine2")
                        else:
                            raise ValueError(f"❌ Unknown or no color detected: {color_rebel}")

                        self.robot_map["rebelline"].sequence_path = "sequences/RebelLine/"
                        self.robot_map["rebelline"].run_task()
                        rebelline_vars["startrebelline"] = 1.0

                    except Exception as e:
                        print(f"⚠️ RebelLine color logic failed: {e}")

                    print(f"📦 Finalized: REBELLINE task started. Vars: {rebelline_vars}")

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
                    rebel1_vars.get("startrebel1") == 0.0
                ):
                    print("📦 REBELLINE dropped to REBEL1")
                    threading.Thread(
                        target=self.robot_map["rebel1"].run_task, 
                        daemon=True
                    ).start()
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
                    rebel2_vars.get("startrebel2") == 0.0
                ):
                    print("📦 REBELLINE dropped to REBEL2")
                    threading.Thread(
                        target=self.robot_map["rebel2"].run_task, 
                        daemon=True
                    ).start()
                    rebel2_vars["startrebel2"] = 1.0

                if rebel2_vars.get("isfinishrebel2", 0.0) == 1.0:
                    print("\n♻️ Resetting REBEL2 variables...")
                    self.robot_map["rebel2"].import_variables()
                    rebel2_vars = self.get_robot_vars("Rebel2")
                time.sleep(1)

            except Exception as e:
                print(f"⚠️ Logic loop error: {e}")
                time.sleep(1)

