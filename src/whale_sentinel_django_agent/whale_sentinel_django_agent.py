from dotenv import load_dotenv
import os
from functools import wraps
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from .wslogger import wslogger
from .wsprotection import Protection
from .wsagent import Agent
import threading
import datetime

class WhaleSentinelDjangoAgent(object):
    """
    Whale Sentinel Django Agent
    """

    def __init__(self):
        """
        Initialize the Whale Sentinel Django Agent

        :param config: Configuration dictionary
        """
        # Load environment variables from .env file
        try:
            load_dotenv()

            LOG_MAX_SIZE = os.getenv("LOG_MAX_SIZE", 10000000)  # in bytes
            LOG_MAX_BACKUPS = os.getenv("LOG_MAX_BACKUPS", 3)  # number of backup files
            WS_GATEWAY_API = os.getenv("WS_GATEWAY_API")
            WS_AGENT_AUTH_TOKEN = os.getenv('WS_AGENT_AUTH_TOKEN')
            WS_AGENT_ID = os.getenv("WS_AGENT_ID")
            WS_AGENT_NAME = os.getenv("WS_AGENT_NAME")
            self.log_max_size = int(LOG_MAX_SIZE)
            self.log_max_backups = int(LOG_MAX_BACKUPS)
            self.ws_gateway_api = WS_GATEWAY_API
            self.ws_agent_auth_token = WS_AGENT_AUTH_TOKEN
            self.agent_id = WS_AGENT_ID
            self.agent_name = WS_AGENT_NAME
            self._initialize()
        except Exception as e:
            wslogger.error(f"Error initializing Whale Sentinel Django Agent: {e}")
            raise

    def _initialize(self):
        """
        Initialize the Whale Sentinel Django Agent
        """
        try:
            if not self.ws_gateway_api:
                raise ValueError("WS_GATEWAY_API must be set")
            if not self.ws_agent_auth_token:
                raise ValueError("WS_AGENT_AUTH_TOKEN must be set")
            if not self.agent_id:
                raise ValueError("WS_AGENT_ID must be set")
            if not self.agent_name:
                raise ValueError("WS_AGENT_NAME must be set")
            Agent.__init__(self)
        except Exception as e:
            wslogger.error(f"Error in Whale Sentinel Django Agent initialization: {e}")

    def whale_sentinel_agent_protection(self):
        def _whale_sentinel_agent_protection(view_func):
            """
            Decorator to protect Django views with Whale Sentinel Protection
            """
            @wraps(view_func)
            def wrapper(request, *args, **kwargs):
                profile = Agent._profile(self)
                if profile is None:
                    wslogger.info("Whale Sentinel Django Agent Protection: No profile found, skipping protection")
                    request_meta_data = Protection.do(self, request)
                    threading.Thread(target=Agent._write_to_storage, args=(self, request_meta_data), daemon=True).start()
                    return view_func(request, *args, **kwargs)
                
                running_mode = profile.get("running_mode", "lite")
                last_run_mode = profile.get("last_run_mode", "lite")
                data_synchronized = profile.get("lite_mode_data_is_synchronized", False)
                data_synchronize_status = profile.get("lite_mode_data_synchronize_status", "fail")
                secure_response_enabled = profile.get("secure_response_headers", {}).get("enable", False)
                
                response = view_func(request, *args, **kwargs)

                if running_mode == "off":
                    return response
                
                if running_mode  == "lite":
                    request_meta_data = Protection.do(self, request)
                    threading.Thread(target=Protection._mode_lite, args=(self, request_meta_data), daemon=True).start()

                if running_mode != "lite" and last_run_mode == "lite" and not data_synchronized and data_synchronize_status == "fail":
                    threading.Thread(target=Agent._synchronize, args=(self, profile), daemon=True).start()

                if running_mode == "monitor":
                    request_meta_data = Protection.do(self, request)
                    threading.Thread(target=Protection._mode_monitor, args=(self, request_meta_data), daemon=True).start()
                
                if running_mode == "protection":
                    request_meta_data = Protection.do(self, request)
                    blocked = Protection._mode_protection(self, profile, request_meta_data)
                    if blocked:
                        wslogger.info("Whale Sentinel Django Agent Protection: Request blocked by Whale Sentinel Protection")
                        return JsonResponse({
                            "msg": "Forbidden: Request blocked by Whale Sentinel Protection.",
                            "time": str(datetime.datetime.now()),
                            "ip": request.META.get("REMOTE_ADDR")
                        }, status=403)

                if secure_response_enabled:
                    response = Protection._secure_response(self, profile, response)

                return response
            return wrapper
        return _whale_sentinel_agent_protection
    