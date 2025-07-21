import grpc
from concurrent import futures

from grpc_interface import robot_controller_pb2
from grpc_interface import robot_controller_pb2_grpc

from controllers.logic_controller import LogicController
from controllers.state_controller import StateController

from config import robots_config
from robots.base_robot import BaseRobot 
from grpc_reflection.v1alpha import reflection


from robots.utils import load_robots

robots = load_robots()
logic = LogicController(robots)
state = StateController(logic.robots)


class RobotControllerService(robot_controller_pb2_grpc.RobotControllerServicer):
    def ConectingSequence(self, request, context):
        msg = state.connect_robots()
        return robot_controller_pb2.Status(message=msg, success=True)
    
    # def Enable(self, request, context): 
       

    def Reference(self, request, context):
        msg = state.reference_robots()
        return robot_controller_pb2.Status(message=msg, success=True)

    def ImportVariables(self, request, context):
        msg = state.import_variables()
        return robot_controller_pb2.Status(message=msg, success=True)

    def StartSequence(self, request, context):
        msg = state.start_logic()

        return robot_controller_pb2.Status(message=msg, success=True)

    def Stop(self, request, context):
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
