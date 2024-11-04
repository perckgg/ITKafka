
from flask import Flask, jsonify,request
from Scanner import ScannerLaptop
from kafka import KafkaProducer
import json
from flask_cors import CORS
import requests
import threading
import time
obj = ScannerLaptop()

class Collector:
    def __init__(self, agent_ip):
        self.agent_ip = agent_ip
        self.data = obj.saveData
        self.status = False

    def send_data_to_agent(self):
        try:
            obj.start()
            producer.send(topic='test', value= obj.saveData)
        except requests.RequestException as e:
            print(f"Error sending data to agent: {e}")
    def start_sending(self, interval=10):#set up time to send scan
        def send_data_periodically():
            while True:
                self.send_data_to_agent()
                time.sleep(interval)
        thread = threading.Thread(target=send_data_periodically)
        thread.daemon = True
        thread.start()
        #self.send_data_to_agent()
    
if __name__ == "__main__":
    config_ip = open("Config.txt","r") 
    server_ip = config_ip.read()
    collector = Collector(agent_ip=server_ip)  
    producer = KafkaProducer(value_serializer=lambda v: json.dumps(v).encode('utf-8'),bootstrap_servers=server_ip)
    while collector.status is False:
        collector.start_sending()
        time.sleep(15)
