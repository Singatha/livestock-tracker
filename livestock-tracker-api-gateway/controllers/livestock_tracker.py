import grpc
from compiled_protos import livestock_pb2
from compiled_protos import livestock_pb2_grpc

def add_livestock(user_id, livestock_type, health_status, group_name, age, expected_growth):
  with grpc.insecure_channel("livestock-tracker-service-backend:50051") as channel:
    stub = livestock_pb2_grpc.LivestockServiceStub(channel)
    livestock = livestock_pb2.AddLivestockRequest(user_id=user_id, livestock_type=livestock_type, health_status=health_status, group_name=group_name, age=age, expected_growth=expected_growth)
    print(livestock)
    return stub.AddLivestock(livestock)
