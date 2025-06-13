from cri_lib import CRIController
import time
import random


class LogicController:
    def __init__(self, robots):
        self.robots = robots
        self.robot_map = {robot.robot_id: robot for robot in robots}

    def get_robot_vars(self, robot_name):
        return self.robot_map[robot_name.lower()].controller.robot_state.variabels
        
    def check_emergency_by_motor_status(self):
        for robot_id, robot in self.robot_map.items():
            if not robot.controller.motors_are_enabled():
                print(f"🛑 Detected disabled motors on {robot_id.upper()} → possible E-STOP")
                return True
        return False

         
    def run_scenario(self):
        print("\n🔁 Starting infinite production loop, waiting for objet")
        
        isObjForScara = False
        isObjForRebelLine = False
        
        while True:
            # =========================
            # 🛑 Check for emergency stop
            # =========================
            if self.check_emergency_by_motor_status():
                print("🚨 Emergency state detected by motor status.")
                while self.check_emergency_by_motor_status():
                    print("🕒 Waiting for all emergency stops to be released...")
                    time.sleep(2)
            print("✅ Emergency stop cleared! Restarting sequence...")
    
            # Reiniciar el sistema como si fuera el arranque inicial
            for robot_id, robot in self.robot_map.items():
                print(f"♻️ Re-importing variables for {robot_id.upper()}")
                robot.import_variables()
    
            isObjForScara = False
            isObjForRebelLine = False

            try:
                scara_vars = self.get_robot_vars("Scara")
                rebelline_vars = self.get_robot_vars("RebelLine")
                rebel1_vars = self.get_robot_vars("Rebel1")
                rebel2_vars = self.get_robot_vars("Rebel2")

                print(f"🔍 Scara variables:  {scara_vars}")
                print(f"\n{'--'*30}")
                print(f"🔍 Rebel Line variables:  {rebelline_vars}")
                print(f"\n{'--'*30}")
                print(f"🔍 Rebel 1 variables:  {rebel1_vars}")
                print(f"\n{'--'*30}")
                print(f"🔍 Rebel 2 variables:  {rebel2_vars}")
                print(f"\n{'=='*30}")
                
                # Randomly trigger SCARA availability
                if not isObjForScara:
                    rand = random.randint(1, 50)
                    if rand % 5 == 0:
                        print(f"🎲 Generated number {rand} is multiple of 5 → SCARA available")
                        isObjForScara = True
                        
                print(f"🎲 Generated number {rand}")
                
                print('========================================================')     
                print(f"Is there object for Rebel Line? --> {isObjForRebelLine} ")
                print(f"Is there object for Scara? --> {isObjForScara} ")
                print('========================================================')
                
                #=====================================================
                #               🤖 SCARA robot logic
                #=====================================================
                if(
                    isObjForScara and
                    not isObjForRebelLine and
                    scara_vars.get("startscara", 0.0) == 0.0
                ):
                    print("🟢 Starting initial SCARA task...")
                    self.robot_map["scara"].run_task()
                    isObjForScara = False
                  
                #=====================================================
                #          🔄 SCARA triggers REBELLINE flag
                #=====================================================
                if scara_vars.get("posdropobjscara") == 1.0:
                    isObjForRebelLine = True
                    print("📦 SCARA dropped object → there is objet for Rebel Line")

                if rebelline_vars.get("posreciverebelline1") == 1.0 or rebelline_vars.get("posreciverebelline2") == 1.0 :
                    isObjForRebelLine = False
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
                if (
                    isObjForRebelLine and
                    rebelline_vars.get("startrebelline") == 0.0 and
                    scara_vars.get("startscara") == 1.0
                ):
                    
                    print("📦 Detected object dropped by SCARA → REBELLINE")
                    print(f"Rebel variables: {rebelline_vars}")
                 
                    obj_type = random.randint(1, 100)
                    print(f"RAMDOM NUMBER IS: {obj_type}")

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
                    rebelline_vars["startrebelline"] = 1.0
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
                if (
                    rebelline_vars.get("posdropobjrebellinetorebel1") == 1.0 and
                #    rebelline_vars.get("lastprogram") == "RebelLine1" and
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
