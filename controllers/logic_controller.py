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
DOOR_OPEN_POS = 100.0 

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
                print(f"\033[91m🛑 Detected disabled motors on {robot_id.upper()} → possible E-STOP\033[0m")
                return True
        return False
    
    def run_task_with_feedback(self, robot_key):
        robot = self.robot_map[robot_key]
        print(f"\033[96m🚀 [{robot_key.upper()}] Running task: {robot.program_name}\033[0m")
        robot.run_task()

    def execute_rebelline_end_program(self, lastProgram):
        if lastProgram == "RebelLineSafePos1":
            self.robot_map["rebelline"].program_name = "RebelLineEnd1.xml"
            print("\033[92m📦 Proceeding with: RebelLineEnd1.xml (WHITE/ORANGE)\033[0m")
        elif lastProgram == "RebelLineSafePos2":
            self.robot_map["rebelline"].program_name = "RebelLineEnd2.xml"
            print("\033[92m📦 Proceeding with: RebelLineEnd2.xml (BLUE)\033[0m")
        self.robot_map["rebelline"].sequence_path = "sequences/RebelLine/"
        print(f"\033[96m🚀 Launching REBELLINE program: {self.robot_map['rebelline'].program_name}\033[0m")
        self.robot_map["rebelline"].run_task()


    def print_robot_variables_periodically(self):
        while True:
            try:
                for name in ["Scara", "RebelLine", "Rebel1", "Rebel2"]:
                    vars_ = self.get_robot_vars(name)
                    print(f"🔍 {name} variables:  {vars_}\n{'--'*30}")

            except Exception as e:
                print(f"⚠️ Error while printing robot variables: {e}")
            time.sleep(5)
            
    def format_ball_color(self, color: str) -> str:
        """Returns the given color name with ANSI terminal color formatting."""
        if color == "orange":
            return f"\033[33m{color}\033[0m"  # orange/yellow
        elif color == "white":
            return f"\033[97m{color}\033[0m"  # bright white
        elif color == "blue":
            return f"\033[34m{color}\033[0m"  # blue
        else:
            return color  # no color formatting

    def run_scenario(self):
        print("\n🔁 Starting infinite production loop, waiting for objet")

        

        # threading.Thread(target=self.print_robot_variables_periodically, daemon=True).start()

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
            recent_scara = detected_scara and (now - ts_scara < 2.5)
            recent_rebel = detected_rebel and (now - ts_rebel < 1.5)

            isObjForScara = detected_scara
            isObjForRebelLine = detected_rebel
                
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
                    
                    print("\033[96m🔧 [D1 DOOR] Referencing motor...\033[0m")
                    
                    self.d1_door.reference()
                    
                    # TODO: revisar que el D1 no se active a la primera de cambio sino que espere a que el scara esté seguro de que ha cogido la pelota
                    
                    detected_scara, color_scara, timestamp  = self.vision.get_detection("URL_scara")

                    print(f"🎥 [SCARA CAM] Ball detected? → isObjForScara = {isObjForScara}")
                    print(f"🔎 [SCARA CAM] Raw detection result (detected_scara) → {detected_scara}")
                    print(f"🎨 [SCARA CAM] Detected ball color → {color_scara} (It's not necessary)")
                    print('========================================================')
                  
                    # ========== 🎯 SCARA ball detection ==========
                    
                    # Apply orange color (ANSI 33) only if the detected color is 'orange'
                    color_display = self.format_ball_color(color_scara)

                    print(f"""\033[94m🎥 [SCARA CAM] 
                        • Ball detected = {detected_scara}
                        • Color         = {color_display}
                    \033[0m""")

                    
                    print(f"""\033[94m🔄 [D1 DOOR] 
                        • Should move? isObjForScara={isObjForScara}
                        • WaitingConfirm={self.boolWaitingForConfirmBallPickUpScara}
                    \033[0m""")
                    
                    if not isObjForScara and not self.boolWaitingForConfirmBallPickUpScara:
                        print("⏳ No ball detected for SCARA → move D1 door")
                        if self.d1_door:
                            speed = self.d1_door.convertBytesToInt(self.d1_door.sendCommand(self.d1_door.statusSpeed_array), 4)
                            if speed >  -0.5:
                                self.d1_door.move_to_right()
                    else:
                        print("\033[92m✅ Ball detected for SCARA — D1 door stays in place\033[0m")
     
                #=====================================================
                #               🤖 SCARA robot logic
                #=====================================================      
                
                print("\033[96m🔍 [SCARA] Evaluating entry conditions...\033[0m")   
                print(f"""\033[94m📌 [SCARA Conditions]
                    • isObjForScara           = {isObjForScara}
                    • WaitingConfirm          = {self.boolWaitingForConfirmBallPickUpScara}
                    • isObjForRebelLine       = {isObjForRebelLine}
                    • startscara              = {scara_vars.get('startscara')}
                    • WaitingForRebelConfirm = {self.boolWaitingForConfirmBallPickUp}
                \033[0m""")
                print('========================================================')
       
                if (
                    (isObjForScara or self.boolWaitingForConfirmBallPickUpScara) and 
                    not isObjForRebelLine and
                    not self.boolWaitingForConfirmBallPickUp and
                    scara_vars.get("startscara") == 0.0
                    
                ):
                    print("\033[92m🟢 [SCARA] Starting SafePos routine...\033[0m")
                    
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
                            print("\033[93m📝 Loading ScaraRealSafePos.xml...\033[0m")
                            self.robot_map["scara"].program_name = "ScaraRealSafePos.xml"
                            self.robot_map["scara"].sequence_path = "sequences/Scara/"
                            self.robot_map["scara"].run_task()
                            self.boolWaitingForConfirmBallPickUpScara = True
                            print("🤖 Load: ScaraRealSafePos")
                        
                        #--------------------------------------------------------
                        # ⏳ Wait until SCARA confirms reaching SafePos
                        #--------------------------------------------------------
                        
                        # Initialize timer to control how often we print to the console
                        start_time = time.time()

                        # Initialize timer to control how often we print to the console
                        start_time = time.time()

                        # Wait until SCARA reaches SafePos (scarasafepos becomes 1.0)
                        while ScaraSafePos == 0.0:
                            # Refresh variables from the SCARA robot
                            scara_vars = self.get_robot_vars("Scara")
                            ScaraSafePos = scara_vars.get("scarasafepos", 0.0)

                            # Only print to console every 5 seconds to avoid excessive output
                            if time.time() - start_time >= 5:
                                print(f"\033[93m⏳ Waiting SCARA to reach SafePos → current: {ScaraSafePos}\033[0m")
                                start_time = time.time()  # Reset the print timer

                            # Check the variable frequently (every 0.5 seconds)
                            time.sleep(0.5)

                        # Print final confirmation once SCARA has reached SafePos
                        print(f"\033[92m✅ SCARA reached SafePos → final value: {ScaraSafePos}\033[0m")

                        #--------------------------------------------------------
                        # ✅ Phase 2: Confirm if object was picked up successfully
                        #--------------------------------------------------------
                        
                        detected_after_safe_scara, _, ts_scara = self.vision.get_detection("URL_scara")
                        now = time.time()
     
                        if self.boolWaitingForConfirmBallPickUpScara and detected_after_safe_scara and ScaraSafePos == 1.0:
                            self.boolWaitingForConfirmBallPickUpScara = False

                        # if self.boolWaitingForConfirmBallPickUpScara and not detected_after_safe_scara and ScaraSafePos == 1.0:
                        #     not_detected_after_scara = True
                        # elif self.boolWaitingForConfirmBallPickUpScara and detected_after_safe_scara and ScaraSafePos == 1.0:
                        #     self.boolWaitingForConfirmBallPickUpScara = False
                        #     not_detected_after_scara = False

                        print("✅ SafePos reached → checking post-pickup conditions:")

                        print(f"""\033[94m📊 [SCARA Post-Pickup Check]
                            • Detected after SafePos     = {detected_after_safe_scara}
                            • Waiting confirmation flag  = {self.boolWaitingForConfirmBallPickUpScara}
                            • SCARA SafePos value        = {ScaraSafePos}
                        \033[0m""")
                        
                        
                        if ScaraSafePos == 1.0:    # if ScaraSafePos in [1.0, 5.0]:
                            if not detected_after_safe_scara:
                                
                                #--------------------------------------------------------
                                # 🎯 Object successfully picked → proceed to End sequence
                                
                                print("\033[92m🎯 Object picked up → launching ScaraRealEnd.xml\033[0m")
                                self.boolWaitingForConfirmBallPickUpScara = False
                                scara_vars["scarasafepos"] = 0.0
                                print("✅ Object pickup confirmed → proceed with ScaraRealEnd")

                                self.robot_map["scara"].program_name = "ScaraRealEnd.xml"
                                self.robot_map["scara"].sequence_path = "sequences/Scara/"
                                self.robot_map["scara"].run_task()

                            elif not self.boolWaitingForConfirmBallPickUpScara or ScaraSafePos == 5.0:
                                
                                #--------------------------------------------------------
                                # 🔁 Object not picked → retry SafePos sequence
                                
                                print("\033[91m🔁 Ball still present → retrying ScaraRealSafePos.xml\033[0m")
                                scara_vars["scarasafepos"] = 0.0
                                self.boolWaitingForConfirmBallPickUpScara = True

                                self.robot_map["scara"].program_name = "ScaraRealSafePos.xml"
                                self.robot_map["scara"].run_task()

                    except Exception as e:
                        print(f"\033[91m⚠️ [SCARA] Logic error: {e}\033[0m")

                    print("\033[96m🔄 [SCARA] Cycle completed. Ready for next task.\033[0m")
                        
                #=====================================================
                #          🔄 SCARA triggers REBELLINE flag
                #=====================================================
                
                if isObjForRebelLine: 
                    print(f"🎥 [REBEL CAM] Ball detected? → isObjForRebelLine = {isObjForRebelLine}")
                    print(f"🔎 [REBEL CAM] Raw detection result (detected_rebel) → {detected_rebel}")
                    print(f"🎨 [REBEL CAM] Detected ball color → {color_rebel} ")
                    print("📦 SCARA dropped object → there is object for Rebel Line")
                    
                else:
                    print("⚠️ RL camera did NOT detect object → skipping.")

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
                
                # try:
                #     print(f"🎥 Rebel camera detected: {detected_rebel}, color: {color_rebel}")
                # except Exception as e:
                #     detected_rebel, color_rebel = False, None
                #     print(f"⚠️ Rebel camera detection error: {e}")

                #--------------------------------------------------------
                # ⚙️ 2. Validate conditions to start RebelLine sequence
                #--------------------------------------------------------
                print(f"""\033[94m📌 [REBELLINE Conditions]
                    • isObjForRebelLine         = {isObjForRebelLine}
                    • WaitingConfirm            = {self.boolWaitingForConfirmBallPickUp}
                    • startrebelline1           = {rebelline_vars.get('startrebelline1')}
                    • startrebelline2           = {rebelline_vars.get('startrebelline2')}
                    • SCARA posdropobjscara     = {scara_vars.get('posdropobjscara')}
                    • SCARA startscara          = {scara_vars.get('startscara')}
                    • SCARA isfinishscara       = {scara_vars.get('isfinishscara')}
                \033[0m""")
                
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
                                print("\033[93m🎨 Color detected: WHITE or ORANGE → Load RebelLineSafePos1.xml\033[0m")
                                self.robot_map["rebelline"].program_name = "RebelLineSafePos1.xml"
                                rebelline_vars["lastprogram"] = "RebelLineSafePos1"
                                lastProgram = "RebelLineSafePos1"
                                self.boolWaitingForConfirmBallPickUp = True
                                print(f"🤖 Load: RebelLineSafePos1")
                            elif color_rebel == "blue":
                                print("\033[93m🎨 Color detected: BLUE → Load RebelLineSafePos2.xml\033[0m")
                                self.robot_map["rebelline"].program_name = "RebelLineSafePos2.xml"
                                rebelline_vars["lastprogram"] = "RebelLineSafePos2"
                                lastProgram = "RebelLineSafePos2"
                                self.boolWaitingForConfirmBallPickUp = True
                                print(f"🤖 Load: RebelLineSafePos2")
                            else:
                                # ⚠️ Unknown color — allow reattempt without raising
                                print(f"\033[91m⚠️ Unknown color detected: {color_rebel} → Skipping activation\033[0m")

                            self.robot_map["rebelline"].sequence_path = "sequences/RebelLine/"
                            self.robot_map["rebelline"].run_task()
                        
                        #--------------------------------------
                        # ⏳ Wait for robot to reach SafePos
                        #--------------------------------------
                        
                        # Initialize timer to control how often we print to the console
                        start_time = time.time()

                        # Initialize timer to control how often we print to the console
                        start_time = time.time()

                        # Wait until REBELLINE reaches SafePos (safepos becomes 1.0)
                        while safepos == 0.0:
                            # Refresh variables from the RebelLine robot
                            rebelline_vars = self.get_robot_vars("RebelLine")
                            safepos = rebelline_vars.get("safepos", 0.0)

                            # Only print to console every 5 seconds to avoid log flooding
                            if time.time() - start_time >= 5:
                                print(f"\033[93m⏳ Waiting for REBELLINE to reach SafePos → current: {safepos}\033[0m")
                                start_time = time.time()  # Reset the print timer

                            # Check the variable more frequently (every 0.5 seconds)
                            time.sleep(0.5)

                        # Print final confirmation once REBELLINE has reached SafePos
                        print(f"\033[92m✅ REBELLINE reached SafePos → final value: {safepos}\033[0m")


                        # ✅ Phase 2: Check if ball was picked up successfully
                        
                        safepos = rebelline_vars.get("safepos", 0.0)
                        detected_after_safe, color_after_safe, ts = self.vision.get_detection("URL_rebel")
                        now = time.time()
                        
                        print(f"""\033[94m📊 [REBELLINE Post-Pickup Check]
                            • Detected after SafePos     = {detected_after_safe}
                            • Waiting confirmation flag  = {self.boolWaitingForConfirmBallPickUp}
                            • SafePos                    = {safepos}
                            • Color after pickup         = {color_after_safe}
                            • Last program               = {lastProgram}
                        \033[0m""")
                        
                        #--------------------------------------------
                        # 📌 Determine post-SafePos detection status
                        #--------------------------------------------
                            
                        if self.boolWaitingForConfirmBallPickUp and not detected_after_safe and safepos==1.0:
                            not_detected_after = True
                        elif self.boolWaitingForConfirmBallPickUp and detected_after_safe and safepos == 1.0:
                            self.boolWaitingForConfirmBallPickUp = False
                            not_detected_after = False                            
                            
                        if safepos == 1.0:
                            if safepos == 1.0:
                                print(f"📦 Ball not detected after SafePos → not_detected_after = {not_detected_after}")
                                print(f"🕒 Waiting for confirmation flag → boolWaitingForConfirmBallPickUp = {self.boolWaitingForConfirmBallPickUp}")
                            
                            #-------------------------------------------------
                            # 🟢 Ball was picked → proceed with End sequence
                            #-------------------------------------------------
                            
                            if not_detected_after: 
                                self.boolWaitingForConfirmBallPickUp = False
                                safepos = 0.0
                                print(f"🚀 Ball pickup confirmed — proceeding to end sequence")  
                                if lastProgram == "RebelLineSafePos1":
                                    self.robot_map["rebelline"].program_name = "RebelLineEnd1.xml"
                                    print("\033[92m📦 Proceeding with: RebelLineEnd1.xml (WHITE/ORANGE)\033[0m")
                                elif lastProgram == "RebelLineSafePos2":
                                    self.robot_map["rebelline"].program_name = "RebelLineEnd2.xml"
                                    print("\033[92m📦 Proceeding with: RebelLineEnd2.xml (BLUE)\033[0m")
         
                                self.robot_map["rebelline"].sequence_path = "sequences/RebelLine/"
                                print(f"\033[96m🚀 [REBELLINE] Running task: {self.robot_map['rebelline'].program_name}\033[0m")
                                self.robot_map["rebelline"].run_task()
                                rebelline_vars["startrebelline"] = 1.0
                                
                            #---------------------------------------- 
                            # 🔁 Ball still detected → retry SafePos
                            #----------------------------------------
                            
                            elif not self.boolWaitingForConfirmBallPickUp:
                                print(f"🔄 Ball detected after SafePos → reloading sequence")          
                                rebelline_vars["safepos"] = 0.0  
                                self.boolWaitingForConfirmBallPickUp = True
                                
                                if color_after_safe in ["white", "orange"]:
                                    self.robot_map["rebelline"].program_name = "RebelLineSafePos1.xml"
                                    rebelline_vars["lastprogram"] = "RebelLineSafePos1"
                                    print(f"\033[93m📦 Loading program: RebelLineSafePos1.xml\033[0m")
                                    
                                elif color_after_safe == "blue":
                                    self.robot_map["rebelline"].program_name = "RebelLineSafePos2.xml"
                                    rebelline_vars["lastprogram"] = "RebelLineSafePos2"
                                    print(f"\033[93m📦 Loading program: RebelLineSafePos2.xml\033[0m")
                                    
                                print(f"\033[96m🚀 [REBELLINE] Running task: {self.robot_map['rebelline'].program_name}\033[0m")
                                self.robot_map["rebelline"].run_task()
 
                    except Exception as e:
                        print(f"⚠️ RebelLine color logic failed: {e}")
                        
                    #-----------------------------------------    
                    # 🧾 Print updated state after logic ends   
                    #-----------------------------------------
                    
                    print(f"Updated RebelLine variables: {self.get_robot_vars('RebelLine')}")
                    print(f"📦 Finalized: REBELLINE task started. Vars: {rebelline_vars}")
                    
                print("\033[93m Initial variables for Rebels are:\033[0m")
                print(f"Rebel 1 -- {rebelline_vars.get('isfinishrebelline1', 0.0)}")
                print(f"Rebel 2 -- {rebelline_vars.get('isfinishrebelline2', 0.0)}")
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
                if rebelline_vars.get("startrebelline1", 0.0) == 1.0:
                    print(f"""\033[94m🔍 [REBEL1] Execution Conditions
                    • posdropobjrebellinetorebel1 = {rebelline_vars.get('posdropobjrebellinetorebel1')}
                    • startrebel1                 = {rebel1_vars.get('startrebel1')}
                \033[0m""")
                
                if (
                    rebelline_vars.get("posdropobjrebellinetorebel1") == 1.0 and
                    # rebelline_vars.get("lastprogram") == "RebelLine1" and
                    rebel1_vars.get("startrebel1") == 0.0
                ):
                    print("\033[92m📦 [REBEL1] Starting movement task...\033[0m")
                    self.robot_map["rebel1"].run_task()
                    print("\033[96m🟢 [REBEL1] Movement initiated.\033[0m")
                    rebel1_vars["startrebel1"] = 1.0

                if rebel1_vars.get("isfinishrebel1", 0.0) == 1.0:
                    print("\033[96m♻️ [REBEL1] Task finished. Resetting variables...\033[0m")
                    self.robot_map["rebel1"].import_variables()
                    rebel1_vars = self.get_robot_vars("Rebel1")

                #=====================================================
                #                  🤖 REBEL2 robot logic
                #=====================================================
                if rebelline_vars.get("startrebelline2", 0.0) == 1.0:
                    print(f"""\033[94m🔍 [REBEL2] Execution Conditions
                    • posdropobjrebellinetorebel2 = {rebelline_vars.get('posdropobjrebellinetorebel2')}
                    • startrebel2                 = {rebel2_vars.get('startrebel2')}
                \033[0m""")
                    
                if (
                    rebelline_vars.get("posdropobjrebellinetorebel2") == 1.0 and
                    rebel2_vars.get("startrebel2") == 0.0
                ):
                    print("\033[92m📦 [REBEL2] Starting movement task...\033[0m")
                    self.robot_map["rebel2"].run_task()
                    print("\033[96m🟢 [REBEL2] Movement initiated.\033[0m")
                    rebel2_vars["startrebel2"] = 1.0

                if rebel2_vars.get("isfinishrebel2", 0.0) == 1.0:
                    print("\033[96m♻️ [REBEL2] Task finished. Resetting variables...\033[0m")
                    self.robot_map["rebel2"].import_variables()
                    rebel2_vars = self.get_robot_vars("Rebel2")
                time.sleep(1)

            except Exception as e:
                print(f"⚠️ Logic loop error: {e}")
                time.sleep(1)



