from compiled_protos import livestock_pb2
from compiled_protos import livestock_pb2_grpc

class LivestockServiceServicer(livestock_pb2_grpc.LivestockServiceServicer):
	def AddLivestock(self, request, context):
		pass
