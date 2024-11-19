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
            # producer.send(topic=config['kafka']['topic'], value= obj.saveData)
            with open('data.json', 'w') as file:
                json.dump(obj.saveData, file, indent=4)
        except requests.RequestException as e:
            print(f"Error sending data to agent: {e}")

    def start_sending(self, interval=10):  # set up time to send scan
        def send_data_periodically():
            while True:
                self.send_data_to_agent()
                print("sending...")
                time.sleep(interval)
        thread = threading.Thread(target=send_data_periodically)
        thread.daemon = True
        thread.start()
        # self.send_data_to_agent()

# def handle_shutdown():
#     msg = {
#         'computer':obj.saveData['basic_info'].get('computer_name'),
#         'shut_down_at':datetime.datetime.now,
#     }
#     producer.send(topic='shutdown',value=msg)
# atexit.register(handle_shutdown)


def scanning(interval=10):
    while True:
        obj.start()

        # Đọc nội dung hiện tại của file
        try:
            with open('data.json', 'r') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []  # Khởi tạo mảng nếu file chưa tồn tại hoặc có lỗi khi đọc JSON

        # Thêm dữ liệu mới vào mảng
        data.append(obj.saveData)

        # Ghi lại nội dung mới vào file
        with open('data.json', 'w') as file:
            json.dump(data, file, indent=4)

        time.sleep(interval)


if __name__ == "__main__":
    with open("../config.yaml", "r") as file:
        config = yaml.safe_load(file)
    server_ip = config['kafka']['bootstrap_servers']
    collector = Collector(agent_ip=server_ip)
    # producer = KafkaProducer(value_serializer=lambda v: json.dumps(v).encode('utf-8'),bootstrap_servers=server_ip)
    while collector.status is False:
        # collector.start_sending()
        scanning(15)
        # producer.flush()
        # time.sleep(5)
