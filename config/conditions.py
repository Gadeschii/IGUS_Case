# from controllers.igus_controller import BaseRobot
# from cri_lib import CRIController

# controller = CRIController()

# def get_modo_rebel(variables, name):
#     val = int(variables.get("modo_rebel_selector", 1))  # valor que decide el modo
#     modo = 1 if val % 2 == 1 else 2
#     print('este ' + name) 
#     print(variables)
#     print(f"🔢 Modo Rebel calculado: {modo}")
#     return modo

# def start_scara(variables):
#     # Scara siempre se mueve si el modo está en 1 o 2 (por defecto 1)
#     modo = get_modo_rebel(variables, "Scara")
#     return modo in (1, 2)

# def getRobotVariables(robot):
#     return robot.controller.robot_state.variabels

# def start_rebelline1(variables):
#     modo = get_modo_rebel(variables, "RebelLine1")
   
#     if modo == 1 and getRobotVariables('posdropobjscara') == 1:
#         variables["__modo_rebel__"] = modo
#         print("🚀 Lanzando Rebelline 1")
#         return True
#     return False

# def start_rebelline2(variables):
#     modo = get_modo_rebel(variables, "RebelLine2")
#     if modo == 2 and getRobotVariables('posdropobjscara') == 1:
#         variables["__modo_rebel__"] = modo
#         print("🚀 Lanzando Rebelline 2")
#         return True
#     return False

# def start_rebel1(variables):
#     return variables.get('posdropobjrebellinetorebel1', 0) == 1

# def start_rebel2(variables):
#     return variables.get('posdropobjrebellinetorebel2', 0) == 1

# robot_start_conditions = {
#     "Scara": start_scara,
#     "RebelLine1": start_rebelline1,
#     "RebelLine2": start_rebelline2,
#     "Rebel1": start_rebel1,
#     "Rebel2": start_rebel2,
# }
