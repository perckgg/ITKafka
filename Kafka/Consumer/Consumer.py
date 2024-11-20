import yaml
from kafka import KafkaConsumer


if __name__ == "__main__":
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
        topic = config['kafka']['topic']
    consumer = KafkaConsumer(topic,
                             bootstrap_servers='localhost:9092',
                             api_version=(0, 11, 5))

    for message in consumer:
        print(f"{message.value.decode('utf-8')}")
