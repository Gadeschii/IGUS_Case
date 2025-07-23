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

robots = load_robots()
state = StateController(robots)
logic = LogicController(robots, state)



class RobotControllerService(robot_controller_pb2_grpc.RobotControllerServicer):
    def ConectingSequence(self, request, context):
        msg = state.connect_robots()
        return robot_controller_pb2.Status(message=msg, success=True)
    
    # def Enable(self, request, context): 

    def ReferenceSequence(self, request, context):
        msg = state.reference_robots()
        return robot_controller_pb2.Status(message=msg, success=True)
    
    def ReferenceSingle(self, request, context):
        msg = state.reference_robot_by_id(request.robot_id)
        return robot_controller_pb2.Status(message=msg, success="referenced" in msg.lower())


    def ImportVariables(self, request, context):
        msg = state.import_variables()
        return robot_controller_pb2.Status(message=msg, success=True)

    def StartSequence(self, request, context):
        msg = state.start_logic()
        return robot_controller_pb2.Status(message=msg, success=True)

    def PauseSequence(self, request, context):
        msg = state.pause_logic()  
        return robot_controller_pb2.Status(message=msg, success=True)

    def ResumeSequence(self, request, context):
        msg = state.resume_logic()
        return robot_controller_pb2.Status(message=msg, success=True)

    def StopSequence(self, request, context):
        msg = state.shutdown()
        return robot_controller_pb2.Status(message=msg, success=True)

    
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    robot_controller_pb2_grpc.add_RobotControllerServicer_to_server(RobotControllerService(), server)
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
