from kafka import KafkaProducer
import json 
import time 

producer = KafkaProducer(
    bootstrap_servers=['18.224.32.56:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'))

orders = [
    {"order_id": 1, "item": "laptop", "price": 999.99},
    {"order_id": 2, "item": "phone", "price": 699.99},
    {"order_id": 3, "item": "headphones", "price": 199.99}]

for order in orders:
    producer.send('orders', value=order)
    print(f"Sent: {order}")
    time.sleep(1)

producer.flush()
print("All messages sent!")