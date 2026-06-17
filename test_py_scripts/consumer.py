from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'orders',
    bootstrap_servers=['18.224.32.56:9092'],
    auto_offset_reset='earliest',
    value_deserializer=lambda v: json.loads(v.decode('utf-8'))
)

print("Waiting for messages...")
for message in consumer:
    print(f"Received: {message.value}")