import pika
import time
import sys, os
from retry import retry

@retry(pika.exceptions.AMQPConnectionError, delay=10, jitter=(1, 3))
def main():    
    def callback(ch, method, properties, body):
        # This function will be called when a message is received
        print(f"Received message: {body}")

    parameters = pika.URLParameters('amqp://guest:guest@livestock-tracker-message-broker:5672/%2F')
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue='hello')
    channel.basic_consume(queue='hello', on_message_callback=callback, auto_ack=True)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    
    try:
        channel.start_consuming()
    except pika.exceptions.ConnectionClosedByBroker:
        pass


if __name__ == '__main__':
    try:
       main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
           os._exit(0)
