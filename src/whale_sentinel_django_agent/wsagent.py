
import os
import base64
from datetime import datetime, timezone
from .wslogger import wslogger
import requests
import time
import json
import socket
import os, sys, platform, threading, multiprocessing, psutil

class Agent(object):
    def __init__(self):
        """
        Initialize the Whale Sentinel Django Agent
        """
        try:
            ws_auth_string = f"ws-agent:{self.ws_agent_auth_token}"
            ws_base64_auth_string = base64.b64encode(ws_auth_string.encode()).decode()
            self.ws_authentication = ws_base64_auth_string
            self.ip_address = Agent._get_internal_ip()    
            Agent._banner()
            Agent._communication(self)
            Agent._init_storage(self)
        except Exception as e:
            wslogger.error(f"Something went wrong at Agent.__init__.\n Error message - {e}")
            raise
    
    def _banner():
        print(
            r"""
 __    __ _           _        __            _   _            _ 
/ / /\ \ \ |__   __ _| | ___  / _\ ___ _ __ | |_(_)_ __   ___| |
\ \/  \/ / '_ \ / _` | |/ _ \ \ \ / _ \ '_ \| __| | '_ \ / _ \ |
 \  /\  /| | | | (_| | |  __/ _\ \  __/ | | | |_| | | | |  __/ |
  \/  \/ |_| |_|\__,_|_|\___| \__/\___|_| |_|\__|_|_| |_|\___|_|
The Runtime Application Self Protection (RASP) Solution - Created by YangYang-Research                                                            
            """
        )

    def _init_storage(self):
        """
        Initialize the Whale Sentinel Django Agent storage
        """
        try:
            running_directory = os.getcwd()
            storage_directory = os.path.join(running_directory, "whale-sentinel-agent-storage")
            
            os.makedirs(storage_directory, exist_ok=True)
            
            storage_file = os.path.join(storage_directory, "ws-agent-lite.txt")
            if not os.path.exists(storage_file):
                open(storage_file, "w").close()
        except Exception as e:
            wslogger.error(f"Something went wrong at Agent._init_storage.\n Error message - {e}")

    def _remove_storage(self):
        """
        Remove the Whale Sentinel Django Agent storage
        """
        try:
            running_directory = os.getcwd()
            storage_directory = os.path.join(running_directory, "whale-sentinel-agent-storage")
            
            if os.path.exists(storage_directory):
                for file in os.listdir(storage_directory):
                    file_path = os.path.join(storage_directory, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                os.rmdir(storage_directory)
        except Exception as e:
            wslogger.error(f"Something went wrong at Agent._remove_storage.\n Error message - {e}")

    def _write_to_storage(self, data):
        """
        Write data to the Whale Sentinel Django Agent storage
        """
        try:
            running_directory = os.getcwd()
            storage_directory = os.path.join(running_directory, "whale-sentinel-agent-storage")
            
            os.makedirs(storage_directory, exist_ok=True)
            
            storage_file = os.path.join(storage_directory, "ws-agent-lite.txt")
            if not os.path.exists(storage_file):
                Agent._init_storage(self)

            with open(storage_file, "a") as f:
                json.dump(data, f)
                f.write("\n")
        except Exception as e:
            wslogger.error(f"Something went wrong at Agent._write_to_storage.\n Error message - {e}")

    def _read_from_storage(self):
        """
        Read data from the Whale Sentinel Django Agent storage
        """
        try:
            running_directory = os.getcwd()
            storage_directory = os.path.join(running_directory, "whale-sentinel-agent-storage")
            
            os.makedirs(storage_directory, exist_ok=True)
            
            storage_file = os.path.join(storage_directory, "ws-agent-lite.txt")
            if not os.path.exists(storage_file):
                return []

            data_list = []
            with open(storage_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data_list.append(json.loads(line))
                        except json.JSONDecodeError as e:
                            wslogger.error(f"Something went wrong at Agent._read_from_storage.\n Error message - {e}")
            return data_list
        except Exception as e:
            wslogger.error(f"Something went wrong at Agent._read_from_storage.\n Error message - {e}")
            
    def _communication(self):
        """
        Communicate with the Whale Sentinel Gateway Service
        """
        try:
            endpoint_1 = self.ws_gateway_api + "/agent/profile"
            endpoint_2 = self.ws_gateway_api + "/agent/synchronize"
            
            send_data_1 = {
                "payload": {
                    "data": {
                        "agent_id": self.agent_id,
                        "agent_name": self.agent_name,
                    },
                },
                "request_created_at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            }

            mem = psutil.virtual_memory()
            total = mem.total           # Tổng RAM (bytes)
            available = mem.available   # RAM còn trống (bytes)
            used = total - available       # RAM đã dùng (bytes)

            used_percent = round((used / total) * 100, 2)  # Phần trăm RAM đã dùng

            send_data_2 = {
                "payload": {
                    "data": {
                        "agent_id": self.agent_id,
                        "agent_name": self.agent_name,
                        "profile" : {
                            "lite_mode_data_synchronize_status": "none",
                            "lite_mode_data_is_synchronized": False
                        },
                        "host_information": {
                            "ip_address": self.ip_address,
                            "pid": os.getpid(),
                            "run_as": psutil.Process().username(),
                            "executable_path": psutil.Process().exe(),
                            "executable_name": threading.current_thread().name,
                            "executable_version": platform.python_version(),
                            "process_name": multiprocessing.current_process().name,
                            "process_path": os.getcwd(),
                            "process_command": psutil.Process().cmdline(),
                            "platform": platform.system(),
                            "cpu_usage": psutil.cpu_percent(interval=1),
                            "memory_usage": used_percent,
                            "architecture": platform.machine(),
                            "os_name": platform.system(),
                            "os_version": platform.version(),
                            "os_build": platform.release(),
                        }
                    }
                },
                "request_created_at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            }

            gateway_response = Agent._make_call(self, endpoint_1, send_data_1)
            if gateway_response is None:
                wslogger.info("Whale Sentinel Django Agent Protection: Communication with Whale Sentinel Gateway failed")
                for i in range(3):
                    time.sleep(30)
                    wslogger.info(f"Whale Sentinel Django Agent Protection: Attempt communication {i + 1} failed")
                    gateway_response = Agent._make_call(self, endpoint_1, send_data_1)
                    if gateway_response is not None:
                        break
            else:
                wslogger.info("Whale Sentinel Django Agent Protection: Commmunication with Whale Sentinel Gateway successful")
                gateway_response = Agent._make_call(self, endpoint_2, send_data_2)
                if gateway_response is None:
                    wslogger.info("Whale Sentinel Django Agent Protection: Synchronize with Whale Sentinel Gateway failed")
                    for i in range(3):
                        time.sleep(30)
                        wslogger.info(f"Whale Sentinel Django Agent Protection: Attempt Synchronize {i + 1} failed")
                        gateway_response = Agent._make_call(self, endpoint_2, send_data_2)
                        if gateway_response is not None:
                            break
        except Exception as e:
            wslogger.error(f"Something went wrong at Agent._communication.\n Error message - {e}")

    def _profile(self) -> None:
        """
        Get the profile of the Whale Sentinel Django Agent
        """
        try:
            endpoint = self.ws_gateway_api + "/agent/profile"
            data = {
                "payload": {
                    "data": {
                        "agent_id": self.agent_id,
                        "agent_name": self.agent_name,
                    }
                },
                "request_created_at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            }

            gateway_response = Agent._make_call(self, endpoint, data)
            if gateway_response is None:
                wslogger.info("Whale Sentinel Django Agent Protection: Communication with Whale Sentinel Gateway failed")
                return None
            return gateway_response.get("data", {}).get("profile", {})
        except Exception as e:
            wslogger.error(f"Something went wrong at Agent._profile.\n Error message - {e}")
    
    def _detection(self, data) -> None:
        """
        Make a prediction using the Whale Sentinel Gateway Service
        """
        try:
            endpoint = self.ws_gateway_api
            
            gateway_response = Agent._make_call(self, endpoint, data)
            if gateway_response is None:
                wslogger.info("Whale Sentinel Django Agent Protection: Communication with Whale Sentinel Gateway failed")
                return None
            analysis_metrix = gateway_response.get("data", {})
            analysis_result = gateway_response.get("analysis_result", "NORMAL_CLIENT_REQUEST")
            return analysis_metrix, analysis_result
        except Exception as e:
            wslogger.error(f"Something went wrong at Agent._detection.\n Error message - {e}")

    def _synchronize(self, profile) -> None:
        """
        Synchronize the Whale Sentinel Django Agent with the Whale Sentinel Gateway Service
        """
        try:
            endpoint = self.ws_gateway_api
            sync_endpoint = f"{endpoint}/agent/synchronize"
            data_synchronize = Agent._read_from_storage(self)

            mem = psutil.virtual_memory()
            total = mem.total           # Tổng RAM (bytes)
            available = mem.available   # RAM còn trống (bytes)
            used = total - available       # RAM đã dùng (bytes)

            used_percent = round((used / total) * 100, 2)  # Phần trăm RAM đã dùng
            
            for item in data_synchronize:
                progress_status = {
                    "payload": {
                        "data": {
                            "agent_id": self.agent_id,
                            "agent_name": self.agent_name,
                            "profile" : {
                                "lite_mode_data_synchronize_status": "inprogress",
                                "lite_mode_data_is_synchronized": False
                            },
                            "host_information": {
                                "ip_address": self.ip_address,
                                "pid": os.getpid(),
                                "run_as": psutil.Process().username(),
                                "executable_path": psutil.Process().exe(),
                                "executable_name": threading.current_thread().name,
                                "executable_version": platform.python_version(),
                                "process_name": multiprocessing.current_process().name,
                                "process_path": os.getcwd(),
                                "process_command": psutil.Process().cmdline(),
                                "platform": platform.system(),
                                "cpu_usage": psutil.cpu_percent(interval=1),
                                "memory_usage": used_percent,
                                "architecture": platform.machine(),
                                "os_name": platform.system(),
                                "os_version": platform.version(),
                                "os_build": platform.release(),
                            }
                        }
                    },
                    "request_created_at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                }
                gateway_response = Agent._make_call(self, sync_endpoint, progress_status)
                if gateway_response is None:
                    wslogger.info("Whale Sentinel Django Agent Protection: Communication with Whale Sentinel Gateway failed")
                    return None
                gateway_response = Agent._make_call(self, endpoint, item)
                if gateway_response is None:
                    wslogger.info("Whale Sentinel Django Agent Protection: Communication with Whale Sentinel Gateway failed")
                    fail_status = {
                        "payload": {
                            "data": {
                                "agent_id": self.agent_id,
                                "agent_name": self.agent_name,
                                "profile" : {
                                    "lite_mode_data_synchronize_status": "failure",
                                    "lite_mode_data_is_synchronized": False
                                },
                                "host_information": {
                                    "ip_address": self.ip_address,
                                    "pid": os.getpid(),
                                    "run_as": psutil.Process().username(),
                                    "executable_path": psutil.Process().exe(),
                                    "executable_name": threading.current_thread().name,
                                    "executable_version": platform.python_version(),
                                    "process_name": multiprocessing.current_process().name,
                                    "process_path": os.getcwd(),
                                    "process_command": psutil.Process().cmdline(),
                                    "platform": platform.system(),
                                    "cpu_usage": psutil.cpu_percent(interval=1),
                                    "memory_usage": used_percent,
                                    "architecture": platform.machine(),
                                    "os_name": platform.system(),
                                    "os_version": platform.version(),
                                    "os_build": platform.release(),
                                }
                            }
                        },
                        "request_created_at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                    }
                    Agent._make_call(self, sync_endpoint, fail_status)
                    return None
            success_status = {
                "payload": {
                    "data": {
                        "agent_id": self.agent_id,
                        "agent_name": self.agent_name,
                        "profile" : {
                            "lite_mode_data_synchronize_status": "successed",
                            "lite_mode_data_is_synchronized": False
                        },
                        "host_information": {
                            "ip_address": self.ip_address,
                            "pid": os.getpid(),
                            "run_as": psutil.Process().username(),
                            "executable_path": psutil.Process().exe(),
                            "executable_name": threading.current_thread().name,
                            "executable_version": platform.python_version(),
                            "process_name": multiprocessing.current_process().name,
                            "process_path": os.getcwd(),
                            "process_command": psutil.Process().cmdline(),
                            "platform": platform.system(),
                            "cpu_usage": psutil.cpu_percent(interval=1),
                            "memory_usage": used_percent,
                            "architecture": platform.machine(),
                            "os_name": platform.system(),
                            "os_version": platform.version(),
                            "os_build": platform.release(),
                        }
                    }
                },
                "request_created_at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            }
            gateway_response = Agent._make_call(self, sync_endpoint, success_status)
            if gateway_response is None:
                return None
            Agent._remove_storage(self)
            return True
        except Exception as e:
            wslogger.error(f"Something went wrong at Agent._synchronize.\n Error message - {e}")

    def _make_call(self, endpoint, data) -> None:
        """
        Make a call to the Whale Sentinel Gateway Service
        """
        try:
            gateway_response = requests.post(
                url=endpoint,
                headers={
                    "Authorization": f"Basic {self.ws_authentication}",
                    "Content-Type": "application/json"
                },
                json=data,
                verify=self.ws_verity_tls 
            )
            if gateway_response.status_code != 200:
                return None
            response_data = gateway_response.json()
            if response_data.get("status", "Error") != "Success":
                return None
            return gateway_response.json()
        except requests.exceptions.RequestException as e:
            wslogger.error(f"Something went wrong at Agent._make_call.\n Error message - {e}")
        except Exception as e:
            wslogger.error(f"Something went wrong at Agent._make_call.\n Error message - {e}")
    
    def _get_internal_ip() -> None:
        """
        Get the internal IP address of the machine
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                # This IP doesn't need to be reachable
                s.connect(('10.255.255.255', 1))
                ip = s.getsockname()[0]
            except Exception:
                ip = '127.0.0.1'
            finally:
                s.close()
            return ip
        except Exception as e:
            wslogger.error(f"Something went wrong at Agent.get_internal_ip.\n Error message - {e}")