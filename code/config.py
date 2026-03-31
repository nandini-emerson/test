
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EcommerceAttendanceTrackerAgentConfig")

class ConfigError(Exception):
    pass

class APISettings:
    def __init__(self):
        # HRIS_API
        self.HRIS_API_URL = os.getenv("HRIS_API_URL", "https://hris.example.com/api")
        self.HRIS_API_CLIENT_ID = os.getenv("HRIS_API_CLIENT_ID")
        self.HRIS_API_CLIENT_SECRET = os.getenv("HRIS_API_CLIENT_SECRET")
        self.HRIS_API_TOKEN_URL = os.getenv("HRIS_API_TOKEN_URL", "https://hris.example.com/oauth2/token")
        self.HRIS_API_RATE_LIMIT = int(os.getenv("HRIS_API_RATE_LIMIT", 1000))
        if not self.HRIS_API_CLIENT_ID or not self.HRIS_API_CLIENT_SECRET:
            logger.error("Missing HRIS_API credentials.")
            raise ConfigError("HRIS_API_CLIENT_ID and HRIS_API_CLIENT_SECRET are required.")

        # FaceRecognition
        self.FACE_API_URL = os.getenv("FACE_API_URL", "https://facerecognition.example.com/api")
        self.FACE_API_KEY = os.getenv("FACE_API_KEY")
        self.FACE_API_IP_WHITELIST = os.getenv("FACE_API_IP_WHITELIST", "")
        self.FACE_API_RATE_LIMIT = int(os.getenv("FACE_API_RATE_LIMIT", 500))
        if not self.FACE_API_KEY:
            logger.error("Missing FaceRecognition API key.")
            raise ConfigError("FACE_API_KEY is required for FaceRecognition integration.")

        # EmailNotification
        self.EMAIL_API_URL = os.getenv("EMAIL_API_URL", "https://email.example.com/api")
        self.EMAIL_API_KEY = os.getenv("EMAIL_API_KEY")
        self.EMAIL_API_RATE_LIMIT = int(os.getenv("EMAIL_API_RATE_LIMIT", 1000))
        if not self.EMAIL_API_KEY:
            logger.error("Missing EmailNotification API key.")
            raise ConfigError("EMAIL_API_KEY is required for EmailNotification integration.")

        # ShiftScheduler (internal)
        self.SHIFT_SCHEDULER_URL = os.getenv("SHIFT_SCHEDULER_URL", "http://internal-shiftscheduler/api")
        self.SHIFT_SCHEDULER_TOKEN = os.getenv("SHIFT_SCHEDULER_TOKEN", "internal_service_token")
        self.SHIFT_SCHEDULER_RATE_LIMIT = None  # Unlimited

class LLMSettings:
    def __init__(self):
        self.PROVIDER = os.getenv("LLM_PROVIDER", "openai")
        self.MODEL = os.getenv("LLM_MODEL", "gpt-4o")
        self.TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.7))
        self.MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", 2000))
        self.SYSTEM_PROMPT = os.getenv(
            "LLM_SYSTEM_PROMPT",
            "You are the Ecommerce Attendance Tracker Agent. Your role is to help employees and HR staff track, validate, and report attendance in a friendly, accurate, and policy-compliant manner. Always verify identity, follow business rules, and escalate issues as needed."
        )
        self.USER_PROMPT_TEMPLATE = os.getenv(
            "LLM_USER_PROMPT_TEMPLATE",
            "Hi {user_name}, how can I assist you with your attendance today?"
        )
        self.FEW_SHOT_EXAMPLES = [
            "I want to check in for my shift.",
            "Why was my attendance marked as late yesterday?"
        ]

class DomainSettings:
    def __init__(self):
        self.DOMAIN = "ecommerce"
        self.ATTENDANCE_WINDOW_MINUTES = int(os.getenv("ATTENDANCE_WINDOW_MINUTES", 15))
        self.REQUIRED_ABSENCE_REASON = True
        self.ALLOWED_ATTENDANCE_STATUSES = ["On Time", "Late", "Early", "Absent"]
        self.POLICY_COMPLIANCE = True

class SecurityComplianceSettings:
    def __init__(self):
        self.ENCRYPTION = "AES-256"
        self.AUTHENTICATION = "SSO with 2FA"
        self.SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", 30))
        self.PII_MASKING = True
        self.AUDIT_LOGGING = True
        self.GDPR_COMPLIANT = True

class Defaults:
    def __init__(self):
        self.RESPONSE_TIME_MS = int(os.getenv("RESPONSE_TIME_MS", 800))
        self.CONCURRENT_REQUESTS = int(os.getenv("CONCURRENT_REQUESTS", 200))
        self.RESOURCE_CPU = os.getenv("RESOURCE_CPU", "4 vCPUs")
        self.RESOURCE_RAM = os.getenv("RESOURCE_RAM", "16 GB")
        self.CACHE_BACKEND = os.getenv("CACHE_BACKEND", "redis")
        self.NOTIFICATION_RETRY = int(os.getenv("NOTIFICATION_RETRY", 3))

class AgentConfig:
    def __init__(self):
        try:
            self.api = APISettings()
            self.llm = LLMSettings()
            self.domain = DomainSettings()
            self.security = SecurityComplianceSettings()
            self.defaults = Defaults()
        except ConfigError as e:
            logger.critical(f"Configuration error: {e}")
            raise

    def validate(self):
        # Additional validation logic if needed
        pass

# Instantiate config at import time for global access
try:
    config = AgentConfig()
except Exception as e:
    logger.critical(f"Agent configuration failed: {e}")
    raise

# Example usage:
# config.api.HRIS_API_URL
# config.llm.MODEL
# config.domain.ATTENDANCE_WINDOW_MINUTES

