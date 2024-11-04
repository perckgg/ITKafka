
from flask import Flask, jsonify,request
from Scanner import ScannerLaptop
from kafka import KafkaProducer
import json
from flask_cors import CORS
import requests
import threading
import time
app = Flask(__name__)
CORS(app)
obj = ScannerLaptop()
producer = KafkaProducer(value_serializer=lambda v: json.dumps(v).encode('utf-8'),bootstrap_servers='10.229.12.33:9092')
class Collector:
    def __init__(self, agent_ip):
        self.agent_ip = agent_ip
        self.data = obj.saveData
        self.status = False

    def send_data_to_agent(self):
        try:
            obj.start()
            # response = requests.post(f"http://{self.agent_ip}:5000/api/receiveData", json=obj.saveData, timeout=6)
            producer.send(topic='test', value= obj.saveData,timestamp_ms=5000)
            # response.raise_for_status()
            # if response.status_code == 200:
            #     self.status = True
        except requests.RequestException as e:
            print(f"Error sending data to agent: {e}")
    def start_sending(self, interval=10):
        def send_data_periodically():
            while True:
                self.send_data_to_agent()
                time.sleep(interval)
        thread = threading.Thread(target=send_data_periodically)
        thread.daemon = True
        thread.start()
        #self.send_data_to_agent()
    
@app.route("/api/getData",methods=["GET"])
def get_info():
    obj.start()
    result = obj.saveData
    # Call start for each request to refresh the data
    return jsonify(result)
if __name__ == "__main__":
    config_ip = open("config.txt","r")
    server_ip = config_ip.read()
    collector = Collector(agent_ip=server_ip)  # Đặt địa chỉ IP của agent tại đây
    while collector.status is False:
        collector.start_sending()
        time.sleep(15)
    app.run(host="0.0.0.0", port=7000)
