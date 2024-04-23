import pika
import time

def callback(ch, method, properties, body):
    # This function will be called when a message is received
    print(f"Received message: {body}")
time.sleep(60)
# Connection parameters
credentials = pika.PlainCredentials('guest', 'guest')
#connection_params = pika.ConnectionParameters(host="livestock-tracker-message-broker")
queue_name = 'hello'  # Replace with your queue name

# Establish connection
connection = pika.BlockingConnection(pika.ConnectionParameters('livestock-tracker-message-broker', 5672, '/', credentials))
channel = connection.channel()

print('Waiting for messages. To exit press CTRL+C')
# Declare the queue (create if not exists)
channel.queue_declare(queue=queue_name)

# Set up the consumer and specify the callback function
channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

print('Waiting for messages. To exit press CTRL+C')
# Start consuming messages
channel.start_consuming()
