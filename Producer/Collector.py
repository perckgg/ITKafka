from Scanner import ScannerLaptop
from kafka import KafkaProducer
import json
import yaml
import atexit
import requests
import threading
import time
import datetime
obj = ScannerLaptop()

class Collector:
    def __init__(self, agent_ip):
        self.agent_ip = agent_ip
        self.data = obj.saveData
        self.status = False

    def send_data_to_agent(self):
        try:
            obj.start()
            producer.send(topic=config['kafka']['topic'], value= obj.saveData)
        except requests.RequestException as e:
            print(f"Error sending data to agent: {e}")
    def start_sending(self, interval=10):#set up time to send scan
        def send_data_periodically():
            while True:
                self.send_data_to_agent()
                print("sending...")
                time.sleep(interval)
        thread = threading.Thread(target=send_data_periodically)
        thread.daemon = True
        thread.start()
        #self.send_data_to_agent()
def handle_shutdown():
    msg = {
        'computer':obj.saveData['basic_info'].get('computer_name'),
        'shut_down_at':datetime.datetime.now,
    }
    producer.send(topic='shutdown',value=msg)
atexit.register(handle_shutdown)
if __name__ == "__main__":
    with open("config.yaml","r") as file:
        config = yaml.safe_load(file)
    server_ip = config['kafka']['bootstrap_servers']
    collector = Collector(agent_ip=server_ip)  
    producer = KafkaProducer(value_serializer=lambda v: json.dumps(v).encode('utf-8'),bootstrap_servers=server_ip)
    while collector.status is False:
        collector.start_sending()
        producer.flush()
        time.sleep(5)
