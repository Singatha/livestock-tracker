from client import livestock_tracker_client
from compiled_protos import livestock_pb2

client_stub = livestock_tracker_client.get_livestock_tracker_client()

def add_livestock(livestock_type, health_status, group_name, age, expected_growth):
  livestock = livestock_pb2.AddLivestockRequest(livestock_type=livestock_type, health_status=health_status, group_name=group_name, age=age, expected_growth=expected_growth)
  return client_stub.AddLivestock(livestock)
