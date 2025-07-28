import grpc
from concurrent import futures

from grpc_interface import robot_controller_pb2
from grpc_interface import robot_controller_pb2_grpc

from controllers.state_controller import StateController
from controllers.logic_controller import LogicController


from config import robots_config
from robots.base_robot import BaseRobot 
from grpc_reflection.v1alpha import reflection


from robots.utils import load_robots

class RobotControllerService(robot_controller_pb2_grpc.RobotControllerServicer):
    
    def __init__(self, logic, state):
        self.logic = logic
        self.state = state
    
    def ConectingSequence(self, request, context):
        msg = self.state.connect_robots()
        return robot_controller_pb2.Status(message=msg, success=True)
    
    
    def GetConnectionStatuses(self, request, context):
        statuses = []

        for robot in self.state.robots:  
            print(f"🧠 Connection status check: {robot.robot_id} - instance ID: {id(robot)}")
            if hasattr(robot, "is_connected") and callable(robot.is_connected):
                connected = robot.is_connected()
            else:
                connected = False  # fallback for unknown types

            status = robot_controller_pb2.RobotConnectionStatus(
                robot_id=robot.robot_id,
                connected=connected,
                status_message="Connected" if connected else "Disconnected"
            )
            statuses.append(status)
            if hasattr(robot, "controller") and robot.controller:
                print(f"🔎 {robot.robot_id.upper()}: connected={connected}, controller says: {robot.controller.is_connected()}")
            else:
                print(f"🔎 {robot.robot_id.upper()}: connected={connected}, no controller present")

        return robot_controller_pb2.RobotStatusList(statuses=statuses)

    def ReferenceSequence(self, request, context):
        msg = self.state.reference_robots()
        return robot_controller_pb2.Status(message=msg, success=True)
    
    def ReferenceSingle(self, request, context):
        msg = self.state.reference_robot_by_id(request.robot_id)
        return robot_controller_pb2.Status(message=msg, success="referenced" in msg.lower())
    
    
    def GetReferenceStatuses(self, request, context):
        statuses = []

        for robot in self.state.robots:
            try:
                print(f"🧠 Reference Status check: {robot.robot_id} - instance ID: {id(robot)}")
                referenced = robot.is_referenced() if hasattr(robot, "is_referenced") else False
                message = "Referenced" if referenced else "Not Referenced"
            except Exception as e:
                referenced = False
                message = f"❌ Error: {e}"

            statuses.append(robot_controller_pb2.RobotReferenceStatus(
                robot_id=robot.robot_id,
                referenced=referenced,
                reference_message=message
            ))

        return robot_controller_pb2.RobotReferenceList(statuses=statuses)



    def ImportVariables(self, request, context):
        msg = self.state.import_variables()
        return robot_controller_pb2.Status(message=msg, success=True)
    
    def GetImportVariableStatuses(self, request, context):
        statuses = []

        for robot in self.state.robots:
            imported = getattr(robot, "variables_imported", False)

            status = robot_controller_pb2.RobotImportStatus(
                robot_id=robot.robot_id,
                imported=imported,
                status_message="Imported" if imported else "Not Imported"
            )
            statuses.append(status)

        return robot_controller_pb2.RobotImportStatusList(statuses=statuses)


    def StartSequence(self, request, context):
        msg = self.state.start_logic()
        return robot_controller_pb2.Status(message=msg, success=True)

    def PauseSequence(self, request, context):
        msg = self.state.pause_logic()  
        return robot_controller_pb2.Status(message=msg, success=True)

    def ResumeSequence(self, request, context):
        msg = self.state.resume_logic()
        return robot_controller_pb2.Status(message=msg, success=True)

    def StopSequence(self, request, context):
        msg = self.state.shutdown()
        return robot_controller_pb2.Status(message=msg, success=True)

    
def serve():
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    robots = load_robots()
    state_controller = StateController(robots)
    logic_controller = LogicController(robots, state_controller)

    robot_controller_pb2_grpc.add_RobotControllerServicer_to_server(
        RobotControllerService(logic_controller, state_controller), server
    )

    server.add_insecure_port('[::]:50051')
    
    SERVICE_NAMES = (
    robot_controller_pb2.DESCRIPTOR.services_by_name['RobotController'].full_name,
    reflection.SERVICE_NAME,
    )

    reflection.enable_server_reflection(SERVICE_NAMES, server)

    server.start()
    print("✅ gRPC server running on port 50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
