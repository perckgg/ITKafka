from kafka import KafkaConsumer

if __name__ == "__main__":
    with open('../config.yaml', 'r') as file:
        topic = file['kafka']['topic']
    consumer = KafkaConsumer(topic, bootstrap_servers='localhost:9092')

    for message in consumer:
        print(f"{message.value.decode('utf-8')}")
