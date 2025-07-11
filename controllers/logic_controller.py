from cri_lib import CRIController
import time
import random
import threading
import time
from controllers.color_detector import *
from controllers.color_detector import VisionManager
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
        self.boolWaitingForConfirmBallPickUp = False
        self.boolWaitingForConfirmBallPickUpScara = False
        self.vision = VisionManager({
            "URL_scara": RTSP_URL,
            "URL_rebel": RTSP_URL_2
        })

        
        for robot in robots:
            if robot.__class__.__name__ == "D1Motor":
                if getattr(robot, "role", None) == "door":
                    self.d1_door = robot
                elif getattr(robot, "role", None) == "elevator":
                    self.d1_elevator = robot
                    
    def get_robot_vars(self, robot_name): 
        print(robot_name + " variables updated.")
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

            except Exception as e:
                print(f"⚠️ Error while printing robot variables: {e}")
            time.sleep(5)

    def run_scenario(self):
        print("\n🔁 Starting infinite production loop, waiting for objet")

        

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
            
            
            #=====================================================
            #               🎥 Camara vision
            #=====================================================
            detected_scara, _ , ts_scara = self.vision.get_detection("URL_scara")
            detected_rebel, color_rebel, ts_rebel = self.vision.get_detection("URL_rebel")

            now = time.time()
            recent_scara = detected_scara and (now - ts_scara < 1.5)
            recent_rebel = detected_rebel and (now - ts_rebel < 1.5)

            isObjForScara = recent_scara
            isObjForRebelLine = recent_rebel
                
            #=====================================================
            
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
                    # detected_scara, color_scara = detect_ball_and_color(RTSP_URL)
                    
                    # TODO: revisar que el D1 no se active a la primera de cambio sino que espere a que el scara este segiuro de que ha cogido la pelota
                    
                    detected_scara, color_scara, timestamp  = self.vision.get_detection("URL_scara")

                    print(f"🎥 [SCARA CAM] Ball detected? → isObjForScara = {isObjForScara}")
                    print(f"🔎 [SCARA CAM] Raw detection result (detected_scara) → {detected_scara}")
                    print(f"🎨 [SCARA CAM] Detected ball color → {color_scara} (It's not necessary)")
                  
                    # ========== 🎯 SCARA ball detection ==========
                    
                    if not isObjForScara:
                        print("⏳ No ball detected for SCARA → move D1 door")
                        if self.d1_door:
                            # print("SI APAREZCO MAS DE UNA VEZ, NO DEBERÍA PASAR HIJUEPUTA")
                            # print("La HP velocidad es:")
                            # print(self.d1_door.convertBytesToInt(self.d1_door.sendCommand(self.d1_door.statusSpeed_array), 4))
                            # print("La HP posición es:")
                            # print(self.d1_door.convertBytesToInt(self.d1_door.sendCommand(self.d1_door.statusPosition_array), 4))
                            speed = self.d1_door.convertBytesToInt(self.d1_door.sendCommand(self.d1_door.statusSpeed_array), 4)
                            if speed >  -0.5:
                                print("SI APAREZCO MAS DE UNA VEZ, NO DEBERÍA PASAR HIJUEPUTA2")
                                print("La HP velocidad es:")
                                # speed = self.d1_door.convertBytesToInt(self.d1_door.sendCommand(self.d1_door.statusSpeed_array), 4)
                                # print("La HP posición es:")
                                # speed = self.d1_door.convertBytesToInt(self.d1_door.sendCommand(self.d1_door.statusPosition_array), 4)
                                self.d1_door.move_to_right()
                    else:
                        print("✅ ping pong ball detected for SCARA")
                        if self.d1_door:
                            isObjForScara = True
                    
                    # if not isObjForScara:
                    #     try:
                    #         # Get latest detection status and timestamp
                    #         detected_scara, _ , ts_scara  = self.vision.get_detection("URL_scara")
                    #         now = time.time()
                    #         recent_detection = detected_scara and (now - ts_scara) < 1.5
                            
                    #         if not recent_detection:
                    #             print("⏳ No ball detected for SCARA → move D1 door")
                    #             if self.d1_door:
                    #                 # Only open if the door isn't already open (motor not moving)
                    #                 if not(((self.d1_door.convertBytesToInt(self.d1_door.sendCommand(self.d1_door.statusSpeed_array), 4)) > 0.5)):
                    #                     self.d1_door.move_to_right()
                    #         else:
                    #             print("✅ Recent ping pong ball detected for SCARA")
                    #             isObjForScara = True

                            
                    #         # # detected_scara, _ = detect_ball_and_color(RTSP_URL)
                    #         # detected_scara, _ , ts_scara  = self.vision.get_detection("URL_scara")
                    #         # now = time.time()
                    #         # recent_detection = detected_scara and (now - ts_scara) < 1.5
                    #         # if recent_detection:
                    #         #     print("✅ Ping pong ball detected → SCARA task ready")
                    #         #     isObjForScara = True
                    #         #     # 🔒 Move door to closed position
                    #         #     # self.d1_door.move_to_left() 
                    #         #     # self.d1_door.current_position = 0.0
                    #         # else:
                    #         #     print("⏳ No ball yet for SCARA")
                    #         #     # 🚪 Open the door
                    #         #     if not(((self.d1_door.convertBytesToInt(self.d1_door.sendCommand(self.d1_door.statusSpeed_array), 4)) > 0.5)):
                    #         #        self.d1_door.move_to_right() 
    
    
    
                    #     except RuntimeError as e:
                    #         print(f"⚠️ SCARA camera error: {e}")
                            
                    # print("📦 Ball ready for SCARA → SCARA can start its task")

                #=====================================================
                #               🤖 SCARA robot logic
                #=====================================================      
                                
                if (
                    (isObjForScara or self.boolWaitingForConfirmBallPickUpScara) and 
                    not isObjForRebelLine and
                    scara_vars.get("startscara") == 0.0
                    
                    # not detect_ball_and_color(RTSP_URL_2)[0] and
                    # not self.vision.get_detection("URL_rebel")[0] and #not isObjForRebelLine
                ):
                    print("🟢 Starting SCARA SafePos task...")

                    try:
                        #--------------------------------------------------------
                        # 🔄 Refresh SCARA variable state
                        #--------------------------------------------------------
                        
                        scara_vars = self.get_robot_vars("Scara")
                        ScaraSafePos = scara_vars.get("scarasafepos", 0.0)
                        
                        #--------------------------------------------------------
                        # 🚦 Phase 1: Load SafePos program if not already in confirmation mode
                        #--------------------------------------------------------
                        
                        if not self.boolWaitingForConfirmBallPickUpScara:
                            self.robot_map["scara"].program_name = "ScaraRealSafePos.xml"
                            self.robot_map["scara"].sequence_path = "sequences/Scara/"
                            self.robot_map["scara"].run_task()
                            self.boolWaitingForConfirmBallPickUpScara = True
                            print("🤖 Load: ScaraRealSafePos")
                        
                        #--------------------------------------------------------
                        # ⏳ Wait until SCARA confirms reaching SafePos
                        #--------------------------------------------------------
                        
                        while ScaraSafePos == 0.0:
                            time.sleep(3)
                            scara_vars = self.get_robot_vars("Scara")
                            ScaraSafePos = scara_vars.get("scarasafepos", 0.0)
                            print(f"Waiting for SCARA SafePos → current value: {ScaraSafePos}")

                        #--------------------------------------------------------
                        # ✅ Phase 2: Confirm if object was picked up successfully
                        #--------------------------------------------------------
                        
                        detected_after_safe_scara, _, ts_scara = self.vision.get_detection("URL_scara")
                        now = time.time()

                        if self.boolWaitingForConfirmBallPickUpScara and not detected_after_safe_scara and ScaraSafePos == 1.0:
                            not_detected_after_scara = True
                        elif self.boolWaitingForConfirmBallPickUpScara and detected_after_safe_scara and ScaraSafePos == 1.0:
                            self.boolWaitingForConfirmBallPickUpScara = False
                            not_detected_after_scara = False

                        print("✅ SafePos reached → checking post-pickup conditions")
                        print(f"not_detected_after_scara = {not_detected_after_scara}")
                        print(f"boolWaitingForConfirmBallPickUpScara = {self.boolWaitingForConfirmBallPickUpScara}")

                        if ScaraSafePos == 1.0:    # if ScaraSafePos in [1.0, 5.0]:
                            if not_detected_after_scara:
                                
                                #--------------------------------------------------------
                                # 🎯 Object successfully picked → proceed to End sequence
                                
                                self.boolWaitingForConfirmBallPickUpScara = False
                                scara_vars["scarasafepos"] = 0.0
                                print("✅ Object pickup confirmed → proceed with ScaraRealEnd")

                                self.robot_map["scara"].program_name = "ScaraRealEnd.xml"
                                self.robot_map["scara"].sequence_path = "sequences/Scara/"
                                self.robot_map["scara"].run_task()

                            elif not self.boolWaitingForConfirmBallPickUpScara or ScaraSafePos == 5.0:
                                
                                #--------------------------------------------------------
                                # 🔁 Object not picked → retry SafePos sequence
                                
                                print("🔄 Object still present → retrying ScaraRealSafePos")
                                scara_vars["scarasafepos"] = 0.0
                                self.boolWaitingForConfirmBallPickUpScara = True

                                self.robot_map["scara"].program_name = "ScaraRealSafePos.xml"
                                self.robot_map["scara"].run_task()

                    except Exception as e:
                        print(f"⚠️ SCARA logic error: {e}")

                    print("🔄 SCARA completed task flow → ready for next cycle")
                                    
   
                    # scara_vars = self.get_robot_vars("Scara")
                    # ScaraSafePos = rebelline_vars.get("ScaraSafePos", 0.0)
                        
                    # print("🟢 Starting initial Safe SCARA task...")
                    # # time to be sure that the ball was static
                    # time.sleep(4.5) 
                    # self.robot_map["scara"].program_name = "ScaraRealSafePos.xml"
                    # self.robot_map["scara"].run_task()
                    
                    # while ScaraSafePos == 0.0:
                    #     scara_vars = self.get_robot_vars("Scara")
                    #     ScaraSafePos = scara_vars.get("ScaraSafePos", 0.0)
                    #     print (ScaraSafePos)
                    #     time.sleep(3)
                    
                    # ScaraSafePos = scara_vars.get("scarasafepos", 0.0)
                    # detected_after_safe_scara, _ , ts_scara = self.vision.get_detection("URL_scara")
                    # now = time.time()
                    
                    # if self.boolWaitingForConfirmBallPickUpScara and not detected_after_safe_scara and ScaraSafePos==1.0:
                    #     not_detected_after_scara = True
                            
                    # elif self.boolWaitingForConfirmBallPickUpScara and detected_after_safe_scara and ScaraSafePos == 1.0:
                    #     self.boolWaitingForConfirmBallPickUpScara = False
                    #     not_detected_after_scara = False                            
                            
                        
                    # if ScaraSafePos == 1.0 or ScaraSafePos == 5.0:
                    #     print("Entre AL CICLO DESEADO 1")
                    #     print(not_detected_after_scara)
                    #     print(self.boolWaitingForConfirmBallPickUpScara)
                    #     if not_detected_after_scara: 
                    #             self.boolWaitingForConfirmBallPickUpScara = False
                    #             ScaraSafePos = 0.0
                    #             print("Entre AL CICLO DESEADO 2")
                    #             print(f"✅ Ball not detected after SafePos → continue sequence")  
                    #             if lastProgram == "ScaraRealSafePos":
                    #                 self.robot_map["scara"].program_name = "ScaraRealEnd.xml"
                    #                 print("📦 Proceed with: ScaraRealEnd")
         
                    #                 self.robot_map["scara"].sequence_path = "sequences/Scara/"
                    #                 self.robot_map["scara"].run_task()
                                
                    #     elif not self.boolWaitingForConfirmBallPickUpScara or ScaraSafePos == 5.0:
                    #             print(f"🔄 Ball detected after SafePos → reloading sequence")          
                    #             scara_vars["scarasafepos"] = 0.0  # Importante si el mismo safePos debe marcarse de nuevo
                    #             self.boolWaitingForConfirmBallPickUpScara = True
                    #             # Decidir nuevo intento
                    #             self.robot_map["scara"].program_name = "ScaraRealSafePos.xml"
                    #             rebelline_vars["lastprogram"] = "ScaraRealSafePos"
                    #             print("📦 Retry: ScaraRealSafePos")
                            
                                
                    #             self.robot_map["scara"].run_task()    

                    
                    # scara_vars.get("posrecivescara") == 1.0
                    # #isObjForScara = False
                    # print("🔄 Scara received object → there isn't objet for Scara")
                    
                    
                    
                    
                    
                    
                #=====================================================
                #          🔄 SCARA triggers REBELLINE flag
                #=====================================================
                
                # RebelLine camera
                # detected_rebel, color_rebel = detect_ball_and_color(RTSP_URL_2)
                
                if isObjForRebelLine: 
                    print(f"🎥 [REBEL CAM] Ball detected? → isObjForRebelLine = {isObjForRebelLine}")
                    print(f"🔎 [REBEL CAM] Raw detection result (detected_rebel) → {detected_rebel}")
                    print(f"🎨 [REBEL CAM] Detected ball color → {color_rebel} ")
                    print("📦 SCARA dropped object → there is object for Rebel Line")
                    
                else:
                    print("⚠️ RL camera did NOT detect object → skipping.")

                # if rebelline_vars.get("posreciverebelline1") == 1.0 or rebelline_vars.get("posreciverebelline2") == 1.0:
                    
                #     isObjForRebelLine = False     
                #     #isObjForRebelLine = detect_pingpong_presence_color_white2(RTSP_URL_2) and detect_pingpong_presence_color_blue2(RTSP_URL_2) #False
                #     print("🔄 RebelLine received object → there isn't objet for Rebel Line")

                 #---------------Reset SCARA variable---------------------

                if scara_vars.get("isfinishscara", 0.0) == 1.0:
                    print("\n♻️ Resetting SCARA variables...")
                    self.robot_map["scara"].import_variables()
                    # 🔄 Recargar variables después de importarlas
                    scara_vars = self.get_robot_vars("Scara")

                #=====================================================
                #              🤖 REBELLINE robot logic
                #=====================================================

                #---------------------------------------------------------------
                # 📸 1. Camera detection of ball and color from RTSP_URL_2
                #---------------------------------------------------------------
                try:
                    print(f"🎥 Rebel camera detected: {detected_rebel}, color: {color_rebel}")
                except Exception as e:
                    detected_rebel, color_rebel = False, None
                    print(f"⚠️ Rebel camera detection error: {e}")

                #--------------------------------------------------------
                # ⚙️ 2. Validate conditions to start RebelLine sequence
                #--------------------------------------------------------
                if (
                    (isObjForRebelLine  or self.boolWaitingForConfirmBallPickUp) and 
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
                        #--------------------------------------
                        # 🔄 Refresh RebelLine variable state
                        #--------------------------------------
                        
                        rebelline_vars = self.get_robot_vars("RebelLine")
                        safepos = rebelline_vars.get("safepos", 0.0)
                        
                        #-------------------------------------------------------------------------
                        # 🚦 Phase 1: Load SafePos program if not already in confirmation process
                        #-------------------------------------------------------------------------
                        
                        if not self.boolWaitingForConfirmBallPickUp:
                            if color_rebel in ["white", "orange"]:
                                self.robot_map["rebelline"].program_name = "RebelLineSafePos1.xml"
                                rebelline_vars["lastprogram"] = "RebelLineSafePos1"
                                lastProgram = "RebelLineSafePos1"
                                self.boolWaitingForConfirmBallPickUp = True
                                print(f"🤖 Load: RebelLineSafePos1")
                            elif color_rebel == "blue":
                                self.robot_map["rebelline"].program_name = "RebelLineSafePos2.xml"
                                rebelline_vars["lastprogram"] = "RebelLineSafePos2"
                                lastProgram = "RebelLineSafePos2"
                                self.boolWaitingForConfirmBallPickUp = True
                                print(f"🤖 Load: RebelLineSafePos2")
                            else:
                                # ⚠️ Unknown color — allow reattempt without raising
                                # TODO: revisar este "else, True"
                                ##raise ValueError(f"❌ Unknown or no color detected: {color_rebel}")
                                True

                            self.robot_map["rebelline"].sequence_path = "sequences/RebelLine/"
                            self.robot_map["rebelline"].run_task()

                        ##print(f" Safe Position: {safepos}")
                        #print(f" Detected Position: {not_detected_after}")
                        
                        #--------------------------------------
                        # ⏳ Wait for robot to reach SafePos
                        #--------------------------------------
                        
                        while safepos == 0.0:
                            rebelline_vars = self.get_robot_vars("RebelLine")
                            safepos = rebelline_vars.get("safepos", 0.0)
                            print (safepos)
                            time.sleep(3)
                        
                        # ✅ Phase 2: Check if ball was picked up successfully
                        safepos = rebelline_vars.get("safepos", 0.0)
                        detected_after_safe, color_after_safe, ts = self.vision.get_detection("URL_rebel")
                        now = time.time()
                    
                        # not_detected_after = not detected_after_safe and (now - ts) < 5.0    
                        # if ((now-ts)>10) and detected_after_safe:
                        #     self.boolWaitingForConfirmBallPickUp = False
                        
                        #--------------------------------------------
                        # 📌 Determine post-SafePos detection status
                        #--------------------------------------------
                            
                        if self.boolWaitingForConfirmBallPickUp and not detected_after_safe and safepos==1.0:
                            not_detected_after = True
                        elif self.boolWaitingForConfirmBallPickUp and detected_after_safe and safepos == 1.0:
                            self.boolWaitingForConfirmBallPickUp = False
                            not_detected_after = False                            
                            
                        print("Deberìa entrar AL CICLO DESEADO 1") 
                        if safepos == 1.0:
                            print("Entre AL CICLO DESEADO 1")
                            print(not_detected_after)
                            print(self.boolWaitingForConfirmBallPickUp)
                            
                            #-------------------------------------------------
                            # 🟢 Ball was picked → proceed with End sequence
                            #-------------------------------------------------
                            
                            if not_detected_after: 
                                self.boolWaitingForConfirmBallPickUp = False
                                safepos = 0.0
                                print("Entre AL CICLO DESEADO 2")
                                print(f"🚀 Ball pickup confirmed — proceeding to end sequence")  
                                if lastProgram == "RebelLineSafePos1":
                                    self.robot_map["rebelline"].program_name = "RebelLineEnd1.xml"
                                    print("📦 Proceed with: RebelLineEnd1")
                                elif lastProgram == "RebelLineSafePos2":
                                    self.robot_map["rebelline"].program_name = "RebelLineEnd2.xml"
                                    print("📦 Proceed with: RebelLineEnd2")
         
                                self.robot_map["rebelline"].sequence_path = "sequences/RebelLine/"
                                self.robot_map["rebelline"].run_task()
                                rebelline_vars["startrebelline"] = 1.0
                                
                            #---------------------------------------- 
                            # 🔁 Ball still detected → retry SafePos
                            #----------------------------------------
                            
                            elif not self.boolWaitingForConfirmBallPickUp:
                                print(f"🔄 Ball detected after SafePos → reloading sequence")          
                                rebelline_vars["safepos"] = 0.0  # Importante si el mismo safePos debe marcarse de nuevo
                                self.boolWaitingForConfirmBallPickUp = True
                                # Decidir nuevo intento
                                if color_after_safe in ["white", "orange"]:
                                    self.robot_map["rebelline"].program_name = "RebelLineSafePos1.xml"
                                    rebelline_vars["lastprogram"] = "RebelLineSafePos1"
                                    print("📦 Retry: RebelLineSafePos1")
                                    
                                elif color_after_safe == "blue":
                                    self.robot_map["rebelline"].program_name = "RebelLineSafePos2.xml"
                                    rebelline_vars["lastprogram"] = "RebelLineSafePos2"
                                    print("📦 Retry: RebelLineSafePos2")
                                
                                self.robot_map["rebelline"].run_task()
 
                    except Exception as e:
                        print(f"⚠️ RebelLine color logic failed: {e}")
                        
                    #-----------------------------------------    
                    # 🧾 Print updated state after logic ends   
                    #-----------------------------------------
                    
                    print(f"Variables actualizadas rebeline: {self.get_robot_vars('RebelLine')}")
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
                if(rebelline_vars.get("startrebelline1", 0.0) == 1.0):
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
                    print("🟢 Move REBEL1")
                    rebel1_vars["startrebel1"] = 1.0

                if rebel1_vars.get("isfinishrebel1", 0.0) == 1.0:
                    print("\n♻️ Resetting REBEL1 variables...")
                    self.robot_map["rebel1"].import_variables()
                    rebel1_vars = self.get_robot_vars("Rebel1")

                #=====================================================
                #                  🤖 REBEL2 robot logic
                #=====================================================
                if(rebelline_vars.get("startrebelline2", 0.0) == 1.0):
                    print("\n🔍 REVISIÓN PARA REBEL2")
                    print(f"posdropobjrebellinetorebel2 = {rebelline_vars.get('posdropobjrebellinetorebel2')}")
                    print(f"startrebel2 = {rebel1_vars.get('startrebel2')}")
                    print(f"isfinishrebelline2 = {rebelline_vars.get('isfinishrebelline2')}")
                    print(f"lastprogram = {rebelline_vars.get('lastprogram')}")
                if (
                    rebelline_vars.get("posdropobjrebellinetorebel2") == 1.0 and
                    rebel2_vars.get("startrebel2") == 0.0
                ):
                    print("📦 REBELLINE dropped to REBEL2")
                    self.robot_map["rebel2"].run_task()
                    print("🟢 Move REBEL2")
                    rebel2_vars["startrebel2"] = 1.0

                if rebel2_vars.get("isfinishrebel2", 0.0) == 1.0:
                    print("\n♻️ Resetting REBEL2 variables...")
                    self.robot_map["rebel2"].import_variables()
                    rebel2_vars = self.get_robot_vars("Rebel2")
                time.sleep(1)

            except Exception as e:
                print(f"⚠️ Logic loop error: {e}")
                time.sleep(1)



