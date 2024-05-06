from concurrent import futures

import grpc
import psycopg
import pika

from compiled_protos import livestock_pb2
from compiled_protos import livestock_pb2_grpc

class LivestockServiceServicer(livestock_pb2_grpc.LivestockServiceServicer):
    def AddLivestock(self, request, context):
        with psycopg.connect("host=psql-livestock-tracker-service-db dbname=livestockTrackerDB user=postgres password=example") as conn:
            # Open a cursor to perform database operations
            with conn.cursor() as cur:

                # Execute a command: this creates a new table
                cur.execute("INSERT INTO livestock (user_id, livestock_type, health_status, group_name, age, expected_growth) VALUES (%s, %s, %s, %s, %s, %s)",(request.user_id, request.livestock_type, request.health_status, request.group_name, request.age, request.expected_growth))

                # Make the changes to the database persistent
                conn.commit()

        credentials = pika.PlainCredentials('guest', 'guest')
        queue_name = 'hello'  # Replace with your queue name

        # Establish connection
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='livestock-tracker-message-broker', port=5672, credentials=credentials))
        channel = connection.channel()

        channel.queue_declare(queue=queue_name)
        channel.basic_publish(exchange='', routing_key='hello', body="Hello World !")
        print(" [x] Sent 'Hello World!'")
        connection.close()

        return livestock_pb2.AddLivestockResponse(message="Livestock added successfully")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    livestock_pb2_grpc.add_LivestockServiceServicer_to_server(LivestockServiceServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
