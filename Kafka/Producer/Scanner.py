import platform
import psutil
import datetime
import socket
import re
import time
import subprocess
from collections import defaultdict

try:
    import pyopencl
except ImportError:
    pyopencl = None

if platform.system() == "Windows":
    import winreg


def get_size(bytes):
    """Return float representing GBs of bytes input"""
    return round(bytes / 1024**3, 2)


def parse_install_date(install_date):
    try:
        # Try parsing the standard YYYYMMDD format
        if re.match(r"^\d{8}$", str(install_date)):
            return datetime.datetime.strptime(str(install_date), "%Y%m%d").strftime("%Y-%m-%d")
        # If the format is not recognized, default to "undefined"
        else:
            return "undefined"
    except ValueError:
        return "undefined"


def get_computer_type(computer_code):
    """
    Convert SMBIOS Memory Type code to description.
    """
    computer_types = {
        '0': 'Unknown',
        '1': 'Desktop',
        '2': 'Mobile',
        '3': 'Workstation',
        '4': 'Enterprise Server',
        '5': 'SOHO Server',
        '6': 'Appliance PC',
        '7': 'Performance Server',
        '8': 'Maximum',
    }
    return computer_types.get(computer_code, 'Unknown')


def get_ram_type(smbios_memory_type_code):
    """
    Convert SMBIOS Memory Type code to description.
    """
    memory_types = {
        '24': 'DDR3',
        '26': 'DDR4',
    }
    return memory_types.get(smbios_memory_type_code, 'Unknown')


def get_form_factor_description(form_factor_code):
    form_factors = {
        "0": "Unknown",
        "1": "Other",
        "2": "SIP",
        "3": "DIP",
        "4": "ZIP",
        "5": "SOJ",
        "6": "Proprietary",
        "7": "SIMM",
        "8": "DIMM",
        "9": "TSOP",
        "10": "PGA",
        "11": "RIMM",
        "12": "SODIMM",
        "13": "SRIMM",
        "14": "SMD",
        "15": "SSMP",
        "16": "QFP",
        "17": "TQFP",
        "18": "SOIC",
        "19": "LCC",
        "20": "PLCC",
        "21": "BGA",
        "22": "FPBGA",
        "23": "LGA"
    }
    return form_factors.get(form_factor_code, "Unknown")


def foo(hive, flag):
    aReg = winreg.ConnectRegistry(None, hive)
    aKey = winreg.OpenKey(
        aReg,
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        0,
        winreg.KEY_READ | flag,
    )

    count_subkey = winreg.QueryInfoKey(aKey)[0]

    software_list = []

    for i in range(count_subkey):
        software = {}
        try:
            asubkey_name = winreg.EnumKey(aKey, i)
            asubkey = winreg.OpenKey(aKey, asubkey_name)
            software["name"] = winreg.QueryValueEx(asubkey, "DisplayName")[0]

            try:
                software["version"] = winreg.QueryValueEx(
                    asubkey, "DisplayVersion")[0]
            except EnvironmentError:
                software["version"] = "undefined"
            try:
                software["publisher"] = winreg.QueryValueEx(
                    asubkey, "Publisher")[0]
            except EnvironmentError:
                software["publisher"] = "undefined"
            try:
                install_date = winreg.QueryValueEx(asubkey, "InstallDate")[0]
                software["install_date"] = parse_install_date(install_date)
            except EnvironmentError:
                software["install_date"] = "undefined"
            try:
                size_kb = winreg.QueryValueEx(asubkey, "EstimatedSize")[0]
                software["size"] = round(size_kb / 1024, 2)  # Convert KB to MB
            except EnvironmentError:
                software["size"] = "undefined"
            software_list.append(software)
        except EnvironmentError:
            continue

    return software_list


def format_uptime(seconds):
    """Formats uptime in the format days:hours:minutes:seconds"""
    delta = datetime.timedelta(seconds=seconds)
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}:{hours:02}:{minutes:02}:{seconds:02}"


def get_uptime():
    boot_time_timestamp = psutil.boot_time()
    uptime_seconds = int(time.time() - boot_time_timestamp)
    formatted_uptime = format_uptime(uptime_seconds)
    return formatted_uptime


class ScannerLaptop:
    def __init__(self) -> None:
        self.saveData = {}
        self.threshold = {
            "cpu_utilization": 3,
            "ram": 50,
            "disk":  50,
            "battery": 100,
            "uptime": 1,
        }

    def check_threshold(self, data):
        notification = []
        cpu_utilization = data.get("cpu", {}).get("ultilization")
        ram = data.get("ram", {}).get("percentage")
        battery = int(data.get("battery", {}).get("percent"))
        uptime = data.get("cpu", {}).get("uptime")
        days_up = int(uptime.split(":")[0])
        if cpu_utilization > self.threshold.get("cpu_utilization"):
            notification.append("CPU utilization is too high")
        if ram > self.threshold.get("ram"):
            notification.append("RAM utilization is too high")
        if battery < self.threshold.get("battery"):
            notification.append("Battery is low")
        if days_up >= self.threshold.get("uptime"):
            notification.append("Uptime is too high")
        return notification

    def start(self):
        basic_info = self.get_basic_info()
        warnings = self.check_threshold(basic_info)
        # software_list = self.get_softwares()
        # self.saveData = {**basic_info, "software": software_list}
        self.saveData = {**basic_info, "warnings": warnings}

    def get_basic_info(self):
        # hard_disk = self.get_harddrive_info()
        battery = psutil.sensors_battery()
        cpu_info = self.get_cpu_info()  # Get CPU information
        gpu_info = self.get_gpu_info()  # Get GPU information
        ram_info = self.get_ram_info()  # Get RAM information
        network_info = self.get_network_info()  # Get network information
        boot_time_timestamp = psutil.boot_time()
        physical_disks = self.get_physical_disk_info()
        softwares = self.get_softwares()
        boot_time = datetime.datetime.fromtimestamp(boot_time_timestamp).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        system_info = self.get_system_info()
        total_mem_used = self.get_total_memory_usage()
        return {
            "basic_info": {
                "computer_name": platform.node(),
                "OS": f"{platform.system()} {platform.release()} {platform.version()}",
                "boot_time": boot_time,
                "producer": system_info.get("producer"),
                "system_model": system_info.get("system_model"),
                "bios_version": system_info.get("bios_version"),
                "mother_board": system_info.get("mother_board"),
                "system_type": system_info.get("system_type"),
                "serial_number": system_info.get("serial_number"),
                "computer_type": system_info.get("computer_type")
            },
            "cpu": cpu_info,
            "gpu": gpu_info,
            "network": network_info,
            "ram": ram_info,
            # "hard_drive": hard_disk,
            "battery": {
                "percent": str(battery.percent) if battery else "0",
                "power_plugged": battery.power_plugged if battery else True,
            },
            "physical_disks": {
                "disk_list": physical_disks,
                "total_memory_used": total_mem_used
            },
            "software": softwares,

        }

    def get_softwares(self):
        software_list = (
            foo(winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_32KEY)
            + foo(winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_64KEY)
            + foo(winreg.HKEY_CURRENT_USER, 0)
        )
        # make software list unique by the name of the software
        software_list = {
            v["name"]: v for v in software_list}.values()  # unique
        soft_list = list(software_list)
        soft_list = soft_list[1:10]
        soft_list = list(
            filter(lambda x: 1 & 1 and x['publisher'] != 'undefined', soft_list))
        return soft_list

    def get_gpu_info(self):
        if pyopencl is None:
            return []
        gpu_info = []
        platforms = pyopencl.get_platforms()
        if not platforms:
            return []
        for platform in platforms:
            for device in platform.get_devices():
                if pyopencl.device_type.to_string(device.type) == 'ALL | GPU':
                    gpu_info.append({
                        "name": device.name,
                        "vendor": device.vendor,
                        "version": device.version,
                        "driver_version": device.driver_version,
                        "global_memory": get_size(device.global_mem_size),
                        "max_clock_speed": device.max_clock_frequency,
                        "compute_units": device.max_compute_units
                    })
        return gpu_info

    def get_cpu_nameandsockets(self):
        result = {}
        try:
            # Run wmic command to get the number of CPU sockets
            if platform.system() == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                result = subprocess.check_output(
                    "wmic cpu get SocketDesignation,Name", startupinfo=startupinfo, shell=True).decode()
                lines = result.split('\n')[1:]
                for line in lines:
                    parts = re.split(r'\s{2,}', line.strip())
                    if len(parts) == 2:
                        name, socket = parts
                        result = {
                            "socket": 1,
                            "description": name
                        }
                # Count the number of unique sockets

                return result
        except subprocess.CalledProcessError as e:
            return f"Error: {str(e)}"

    def get_cpu_info(self):
        # CPU Utilization and basic information
        cpu_percent_total = 0
        for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
            cpu_percent_total += percentage
        cpu_percent = cpu_percent_total / len(
            psutil.cpu_percent(percpu=True, interval=1)
        )
        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_count_physical = psutil.cpu_count(logical=False)
        cpu_freq = psutil.cpu_freq()
        socket_cpu = self.get_cpu_nameandsockets()
        socket = socket_cpu.get("socket")
        cpu_description = socket_cpu.get("description")
        cpu_info = {
            "name": platform.processor(),
            "description": cpu_description,
            "max_speed": int(cpu_freq.max) if cpu_freq else "undefined",
            "cores": cpu_count_physical,
            "logical_processors": cpu_count_logical,
            "uptime": str(get_uptime()),
            "processes": len(psutil.pids()),
            "sockets": socket,
            "ultilization": cpu_percent,
            "machine": platform.machine()
        }
        return cpu_info

    def get_ram_info(self):
        svmem = psutil.virtual_memory()
        try:
            if platform.system() == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                result = subprocess.check_output(
                    "wmic memorychip get BankLabel, Capacity, Speed, Manufacturer, SerialNumber, FormFactor,SMBIOSMemoryType", startupinfo=startupinfo, shell=True).decode()
                lines = result.strip().split('\n')[1:]  # Skip the header line
                ram_info = []
                for line in lines:
                    parts = re.split(r'\s{2,}', line.strip())
                    if len(parts) >= 7:
                        bank_label, capacity, form_factor, manufacturer, serial_number, ram_type, speed = parts
                        ram_info.append({
                            "bank_label": bank_label,
                            "capacity": get_size(int(capacity)),
                            "speed": speed,
                            "manufacturer": manufacturer,
                            "serial_number": serial_number,
                            "form_factor": get_form_factor_description(form_factor),
                            "ram_type": get_ram_type(ram_type)
                        })
            return {
                "total": get_size(svmem.total),
                "used": get_size(svmem.used),
                "percentage": svmem.percent,
                "details": ram_info
            }
        except subprocess.CalledProcessError as e:
            return f"Error: {str(e)}"

    def get_ssid(self):
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            result = subprocess.check_output(
                "netsh wlan show interfaces", startupinfo=startupinfo, shell=True).decode()
            ssid = None
            lines = result.strip().split('\n')[1:]
            for line in lines:
                if "SSID" in line:
                    ssid = line.split(":")[1].strip()
                    break
            return ssid
        except Exception as e:
            return str(e)

    def to_mbps(self, status):
        return round(status / 1000000, 2)

    def get_ethernet_info(self):
        try:
            if platform.system() == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                result = subprocess.check_output(
                    "wmic nic where NetEnabled=true get Name,Speed", startupinfo=startupinfo, shell=True).decode()
                interface_info = []
                lines = result.strip().split('\n')[1:]
                for line in lines:
                    if "Name" not in line and line.strip() != "":
                        parts = line.split()
                        speed = parts[-1]
                        name = " ".join(parts[:-1])
                        interface_info.append(
                            {"icname": name, "cspeed": self.to_mbps(int(speed))})
            return interface_info
        except Exception as e:
            return "Cannot get Ethernet information"

    def get_network_info(self):
        # Get IP and MAC address
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        mac_address = None
        connection_type = "unknown"
        internet_card = self.get_ethernet_info()
        # Get SSID
        ssid = self.get_ssid()
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == psutil.AF_LINK:
                    mac_address = addr.address
                if addr.family == socket.AF_INET and psutil.net_if_stats()[interface].isup:
                    if "wi-fi" in interface.lower() or "wlan" in interface.lower():
                        connection_type = "Wi-Fi"
                        break
                    elif "ethernet" in interface.lower():
                        connection_type = "Ethernet"
                        break
                    elif "local area connection* 1" in interface.lower() or "local area connection* 2" in interface.lower():
                        connection_type = "LAN"
                        break
                    elif interface == "Loopback Pseudo-Interface 1" and ssid is not None:
                        connection_type = "Wi-Fi"
                        break
                    else:
                        connection_type = "Ethernet"
            if connection_type != "unknown":
                break  # if connection type is identified, break the loop
        return {
            "ip": ip_address,
            "mac": mac_address,
            "ssid": ssid if connection_type == "Wi-Fi" else None,
            "connection_type": connection_type,
            "inet_card": internet_card[0].get("icname"),
            "inet_card_speed": int(internet_card[0].get("cspeed"))
        }
    # def get_harddrive_info(self):

    #     partitions = psutil.disk_partitions()
    #     hard_disk = [
    #         {
    #             "label": partition.device.split(":")[0],
    #             "total": get_size(psutil.disk_usage(partition.mountpoint).total),
    #             "usage": get_size(psutil.disk_usage(partition.mountpoint).used),
    #             "free": get_size(psutil.disk_usage(partition.mountpoint).free),
    #             "percent": psutil.disk_usage(partition.mountpoint).percent,
    #             "mountpoint": partition.mountpoint,
    #             "file_system_type": partition.fstype,
    #         }
    #         for partition in partitions
    #     ]
    #     return hard_disk
    def get_total_memory_usage(self):
        partitions = psutil.disk_partitions()
        # Tính tổng dung lượng `usage` của tất cả các ổ đĩa
        total_usage = sum(psutil.disk_usage(
            partition.mountpoint).used for partition in partitions)
        # Chuyển đổi tổng dung lượng sang đơn vị dễ đọc hơn, ví dụ như GB
        total_usage_readable = get_size(total_usage)
        return total_usage_readable

    def get_physical_disk_info(self):
        # Lấy thông tin ổ cứng vật lý
        hard_drives = []

        if platform.system() == "Windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            disk_command = "wmic diskdrive get model,size,deviceid,index,InterfaceType,Status,FirmwareRevision,mediaType,serialNumber,partitions"
            disk_result = subprocess.check_output(
                disk_command, startupinfo=startupinfo, shell=True).decode().strip()

            # Lấy thông tin phân vùng
            partition_command = "wmic partition get deviceid,diskindex,size"
            partition_result = subprocess.check_output(
                partition_command, startupinfo=startupinfo, shell=True).decode().strip()

            # Parse the output of the disk command
            disk_lines = disk_result.split('\n')[1:]
            partition_lines = partition_result.split('\n')[1:]

            # Group partitions by disk index
            partitions_by_disk = defaultdict(list)
            for partition in partition_lines:
                parts = re.split(r'\s{2,}', partition.strip())
                if len(parts) == 3:
                    partition_deviceid, partition_diskindex, partition_size = parts
                    partitions_by_disk[partition_diskindex].append({
                        "index": f"Partition #{len(partitions_by_disk[partition_diskindex])}",
                        # Convert size to GB
                        "size": get_size(int(partition_size))
                    })
            # Process each disk and add corresponding partitions
            for disk in disk_lines:
                parts = re.split(r'\s{2,}', disk.strip())
                if len(parts) >= 9:
                    deviceid, firmware, disk_index, interface_type, media_type, model, partitions_num, serial_number, size, status = parts

                    hard_drives.append(
                        {
                            # Remove the prefix "\\\\.\\PHYSICALDRIVE"
                            "deviceid": deviceid[4:],
                            "firmware": firmware,
                            "index": disk_index,
                            "interface_type": interface_type,
                            "media_type": media_type,
                            "model": model,
                            "number_of_partitions": int(partitions_num),
                            "serial_number": serial_number,
                            "size": get_size(int(size)),  # Convert size to GB
                            "status": status,
                            # Add partitions
                            "partitions": partitions_by_disk[disk_index]
                        }
                    )

        return hard_drives

    def get_system_info(self):
        result = {}
        if platform.system() == "Windows":
            try:
                command1 = "wmic computersystem get model,manufacturer,systemtype,PCsystemType"
                command2 = "wmic baseboard get product, serialnumber,version"
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                output1 = subprocess.check_output(
                    command1, startupinfo=startupinfo, shell=True).decode().strip()
                output2 = subprocess.check_output(
                    command2, startupinfo=startupinfo, shell=True).decode().strip()
                lines1 = output1.split('\n')[1:]
                lines2 = output2.split('\n')[1:]
                for line in lines1:
                    parts = re.split(r'\s{2,}', line.strip())
                    if len(parts) == 4:
                        model, manufacturer, computer_type, system_type = parts
                        result = {
                            "producer": model,
                            "system_model": manufacturer,
                            "system_type": system_type,
                            "computer_type": get_computer_type(computer_type)
                        }
                for line in lines2:
                    parts = re.split(r'\s{2,}', line.strip())
                    if len(parts) == 3:
                        product, serial_number, version = parts
                        result.update({
                            "mother_board": product,
                            "serial_number": serial_number,
                            "bios_version": version
                        })
                return result
            except subprocess.CalledProcessError as e:
                return f"Error: {str(e)}"
