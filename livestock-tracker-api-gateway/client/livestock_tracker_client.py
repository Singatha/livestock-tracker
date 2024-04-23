import grpc
from compiled_protos import livestock_pb2
from compiled_protos import livestock_pb2_grpc


def get_livestock_tracker_client():
       with grpc.insecure_channel("livestock-tracker-service-backend:50051") as channel:
              stub = livestock_pb2_grpc.LivestockServiceStub(channel)
