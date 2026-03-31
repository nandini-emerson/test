
import os
import logging
import asyncio
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator, ValidationError, constr
from dotenv import load_dotenv
import openai
import re

# Load environment variables
load_dotenv()

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("EcommerceAttendanceTrackerAgent")

# Configuration management
class Config:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY is not set in environment variables.")
        raise EnvironmentError("OPENAI_API_KEY is required for LLM integration.")

    LLM_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2000
    SYSTEM_PROMPT: str = (
        "You are the Ecommerce Attendance Tracker Agent. Your role is to help employees and HR staff track, validate, "
        "and report attendance in a friendly, accurate, and policy-compliant manner. Always verify identity, follow "
        "business rules, and escalate issues as needed."
    )
    USER_PROMPT_TEMPLATE: str = "Hi {user_name}, how can I assist you with your attendance today?"
    MAX_TEXT_LENGTH: int = 50000
    MIN_TEXT_LENGTH: int = 1

# Pydantic models for input validation
class TextInput(BaseModel):
    user_name: constr(strip_whitespace=True, min_length=1, max_length=100)
    employee_id: constr(strip_whitespace=True, min_length=1, max_length=50)
    content: constr(strip_whitespace=True, min_length=1, max_length=Config.MAX_TEXT_LENGTH)
    input_type: str = Field(default="text", pattern="^(text|image)$")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Content must not be empty.")
        if len(v) > Config.MAX_TEXT_LENGTH:
            raise ValueError(f"Content exceeds maximum allowed length ({Config.MAX_TEXT_LENGTH}).")
        # Remove dangerous characters
        v = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", v)
        return v

class ImageInput(BaseModel):
    user_name: constr(strip_whitespace=True, min_length=1, max_length=100)
    employee_id: constr(strip_whitespace=True, min_length=1, max_length=50)
    image_base64: str
    input_type: str = Field(default="image", pattern="^(text|image)$")

    @field_validator("image_base64")
    @classmethod
    def validate_image(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("Image data must be a non-empty base64 string.")
        if len(v) > 2 * Config.MAX_TEXT_LENGTH:
            raise ValueError("Image data is too large.")
        return v

class AttendanceValidationInput(BaseModel):
    employee_id: constr(strip_whitespace=True, min_length=1, max_length=50)
    check_in_time: datetime
    shift_start_time: datetime
    input_source: str

class ReportRequestInput(BaseModel):
    employee_id: constr(strip_whitespace=True, min_length=1, max_length=50)
    date_range: Tuple[datetime, datetime]
    report_type: str

class NotificationInput(BaseModel):
    recipient: constr(strip_whitespace=True, min_length=1, max_length=100)
    message: constr(strip_whitespace=True, min_length=1, max_length=Config.MAX_TEXT_LENGTH)
    notification_type: str

class AuthInput(BaseModel):
    user_credentials: Dict[str, Any]

# LLM Client Initialization
client = openai.AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

# Supporting Classes
class InputProcessor:
    """
    Handles and parses incoming user inputs (text, images, badge scans), routes to appropriate validation and processing modules.
    """
    async def process_text_input(self, input_data: TextInput, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes text input, extracts intent and entities using LLM.
        """
        try:
            prompt = (
                f"{Config.SYSTEM_PROMPT}\n"
                f"User: {input_data.content}\n"
                "Extract the intent, entities (such as check-in, check-out, absence, report request), and any relevant details. "
                "Return as JSON: {\"intent\": ..., \"entities\": {...}}"
            )
            response = await client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": Config.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=Config.LLM_TEMPERATURE,
                max_tokens=300
            )
            llm_content = response.choices[0].message.content
            # Try to extract JSON from LLM response
            match = re.search(r"\{.*\}", llm_content, re.DOTALL)
            if match:
                import json
                parsed = json.loads(match.group())
                logger.info(f"LLM parsed input: {parsed}")
                return parsed
            else:
                logger.warning("LLM did not return JSON, fallback to default intent extraction.")
                return {"intent": "unknown", "entities": {}}
        except Exception as e:
            logger.error(f"Error processing text input: {e}")
            raise

    async def process_image_input(self, input_data: ImageInput, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes image input for face recognition (stubbed for demo).
        """
        # In production, integrate with FaceRecognition API/service.
        # Here, we simulate a successful face recognition.
        logger.info("Processing image input for face recognition (stubbed).")
        return {"intent": "check_in", "entities": {"identity_verified": True}}

class AttendanceValidator:
    """
    Validates attendance entries against company policies, shift schedules, and employee identity.
    """
    async def validate_check_in(self, employee_id: str, check_in_time: datetime, shift_start_time: datetime, input_source: str) -> Dict[str, Any]:
        """
        Validates check-in time and identity.
        """
        # Business rule: Check-in must be within 15 minutes of shift start
        delta = abs((check_in_time - shift_start_time).total_seconds())
        if delta > 15 * 60:
            logger.info(f"Attendance validation failed for {employee_id}: Late check-in.")
            return {
                "status": "invalid",
                "error_code": "INVALID_ATTENDANCE_ENTRY",
                "message": "Check-in time is outside the allowed window (15 minutes)."
            }
        # Simulate identity validation (should call FaceRecognition or badge scan)
        identity_verified = True  # Stubbed
        if not identity_verified:
            logger.warning(f"Attendance validation failed for {employee_id}: Identity not verified.")
            return {
                "status": "unauthorized",
                "error_code": "UNAUTHORIZED_ACCESS",
                "message": "Employee identity could not be verified."
            }
        logger.info(f"Attendance validated for {employee_id}.")
        return {"status": "valid", "message": "Attendance entry is valid."}

    async def validate_identity(self, employee_id: str, image_data: str) -> bool:
        """
        Validates employee identity via face recognition (stubbed).
        """
        # In production, call FaceRecognition API
        logger.info(f"Identity validated for {employee_id} (stubbed).")
        return True

class ReportGenerator:
    """
    Generates attendance reports (daily, weekly, monthly) for HR and management.
    """
    async def generate_report(self, employee_id: str, date_range: Tuple[datetime, datetime], report_type: str) -> Dict[str, Any]:
        """
        Generates a report for the given employee and date range.
        """
        # In production, fetch data from HRIS_API
        logger.info(f"Generating {report_type} report for {employee_id} from {date_range[0]} to {date_range[1]}.")
        # Stubbed report
        report = {
            "employee_id": employee_id,
            "report_type": report_type,
            "date_range": [date_range[0].isoformat(), date_range[1].isoformat()],
            "attendance_summary": {
                "on_time": 18,
                "late": 2,
                "absent": 1
            }
        }
        return report

class AnomalyDetector:
    """
    Detects and flags suspicious or inconsistent attendance patterns.
    """
    async def detect_anomalies(self, attendance_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detects anomalies in attendance records.
        """
        anomalies = []
        for record in attendance_records:
            if record.get("status") == "late":
                anomalies.append({
                    "type": "late_check_in",
                    "date": record.get("date"),
                    "details": record
                })
        if len(anomalies) > 3:
            logger.warning("Anomaly threshold exceeded, notifying HR.")
            # In production, notify HR via NotificationManager
        return anomalies

class NotificationManager:
    """
    Sends alerts and notifications to employees and HR via email or dashboard.
    """
    async def send_alert(self, recipient: str, message: str, notification_type: str) -> Dict[str, Any]:
        """
        Sends an alert notification.
        """
        # In production, integrate with EmailNotification API
        logger.info(f"Sending {notification_type} alert to {recipient}.")
        # Simulate delivery status
        return {"success": True, "recipient": recipient, "message": message}

    async def send_confirmation(self, recipient: str, message: str, notification_type: str) -> Dict[str, Any]:
        """
        Sends a confirmation notification.
        """
        logger.info(f"Sending {notification_type} confirmation to {recipient}.")
        return {"success": True, "recipient": recipient, "message": message}

class SecurityComplianceManager:
    """
    Handles authentication, authorization, PII masking, audit logging, and ensures compliance.
    """
    async def authenticate_user(self, user_credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Authenticates user via SSO and 2FA (stubbed).
        """
        # In production, integrate with SSO/2FA provider
        logger.info("Authenticating user (stubbed).")
        if user_credentials.get("username") and user_credentials.get("2fa_code"):
            return {"authenticated": True, "user_context": {"user_id": user_credentials["username"]}}
        else:
            logger.warning("Authentication failed.")
            return {"authenticated": False}

    async def authorize_action(self, user_context: Dict[str, Any], action: str) -> bool:
        """
        Authorizes user action (stubbed).
        """
        # In production, check user roles/permissions
        logger.info(f"Authorizing action '{action}' for user {user_context.get('user_id')}.")
        return True

    async def log_event(self, event: Dict[str, Any]) -> None:
        """
        Logs event for audit and compliance.
        """
        logger.info(f"Audit log: {event}")

# Main Agent Class
class Agent:
    """
    Base Agent class.
    """
    pass

class EcommerceAttendanceTrackerAgent(Agent):
    """
    Main agent class for Ecommerce Attendance Tracker.
    """
    def __init__(self):
        self.input_processor = InputProcessor()
        self.attendance_validator = AttendanceValidator()
        self.report_generator = ReportGenerator()
        self.anomaly_detector = AnomalyDetector()
        self.notification_manager = NotificationManager()
        self.security_compliance_manager = SecurityComplianceManager()

    async def process_input(self, input_data: Union[TextInput, ImageInput], input_type: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Routes and processes incoming user input (text/image).
        """
        try:
            if input_type == "text":
                return await self.input_processor.process_text_input(input_data, user_context)
            elif input_type == "image":
                return await self.input_processor.process_image_input(input_data, user_context)
            else:
                logger.error(f"Unsupported input type: {input_type}")
                raise ValueError("Unsupported input type.")
        except Exception as e:
            logger.error(f"Error in process_input: {e}")
            raise

    async def validate_attendance_entry(self, employee_id: str, check_in_time: datetime, shift_start_time: datetime, input_source: str) -> Dict[str, Any]:
        """
        Validates attendance entry against policy and schedule.
        """
        try:
            return await self.attendance_validator.validate_check_in(employee_id, check_in_time, shift_start_time, input_source)
        except Exception as e:
            logger.error(f"Error in validate_attendance_entry: {e}")
            return {
                "status": "error",
                "error_code": "VALIDATION_ERROR",
                "message": str(e)
            }

    async def generate_attendance_report(self, employee_id: str, date_range: Tuple[datetime, datetime], report_type: str) -> Dict[str, Any]:
        """
        Generates attendance reports for specified date range.
        """
        try:
            return await self.report_generator.generate_report(employee_id, date_range, report_type)
        except Exception as e:
            logger.error(f"Error in generate_attendance_report: {e}")
            return {
                "status": "error",
                "error_code": "REPORT_GENERATION_ERROR",
                "message": str(e)
            }

    async def detect_anomalies(self, attendance_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detects suspicious attendance patterns.
        """
        try:
            return await self.anomaly_detector.detect_anomalies(attendance_records)
        except Exception as e:
            logger.error(f"Error in detect_anomalies: {e}")
            return []

    async def send_notification(self, recipient: str, message: str, notification_type: str) -> Dict[str, Any]:
        """
        Sends notifications to users or HR.
        """
        retries = 0
        max_retries = 3
        while retries < max_retries:
            try:
                return await self.notification_manager.send_alert(recipient, message, notification_type)
            except Exception as e:
                retries += 1
                logger.warning(f"Notification send failed (attempt {retries}): {e}")
                await asyncio.sleep(2 ** retries)
        logger.error("Notification send failed after 3 attempts, escalating.")
        # Escalate (stubbed)
        return {"success": False, "error": "Failed to send notification after 3 attempts."}

    async def authenticate_user(self, user_credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Authenticates user via SSO and 2FA.
        """
        try:
            return await self.security_compliance_manager.authenticate_user(user_credentials)
        except Exception as e:
            logger.error(f"Error in authenticate_user: {e}")
            return {"authenticated": False, "error": str(e)}

# FastAPI App
app = FastAPI(
    title="Ecommerce Attendance Tracker Agent API",
    description="API for tracking, validating, and reporting attendance in ecommerce organizations.",
    version="1.0.0"
)

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = EcommerceAttendanceTrackerAgent()

# Exception Handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error_type": "ValidationError",
            "message": "Input validation failed.",
            "details": exc.errors(),
            "tips": [
                "Ensure all required fields are present.",
                "Check for proper JSON formatting (quotes, commas, brackets).",
                "Content must not be empty and within allowed size."
            ]
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_type": "HTTPException",
            "message": exc.detail,
            "tips": [
                "Check endpoint URL and request method.",
                "Ensure authentication headers are set if required."
            ]
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error_type": "InternalServerError",
            "message": "An unexpected error occurred.",
            "details": str(exc),
            "tips": [
                "Check server logs for more details.",
                "Ensure request JSON is well-formed and within size limits."
            ]
        }
    )

# API Endpoints
@app.post("/process_input", response_model=Dict[str, Any])
async def process_input_endpoint(request: Request):
    """
    Endpoint to process user input (text or image).
    """
    try:
        data = await request.json()
        input_type = data.get("input_type", "text")
        user_context = {
            "user_name": data.get("user_name"),
            "employee_id": data.get("employee_id")
        }
        if input_type == "text":
            input_obj = TextInput(**data)
        elif input_type == "image":
            input_obj = ImageInput(**data)
        else:
            raise HTTPException(status_code=400, detail="Unsupported input_type. Must be 'text' or 'image'.")
        result = await agent.process_input(input_obj, input_type, user_context)
        return {"success": True, "result": result}
    except ValidationError as ve:
        logger.error(f"Validation error in /process_input: {ve}")
        raise ve
    except Exception as e:
        logger.error(f"Error in /process_input: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validate_attendance", response_model=Dict[str, Any])
async def validate_attendance_endpoint(input_data: AttendanceValidationInput):
    """
    Endpoint to validate attendance entry.
    """
    try:
        result = await agent.validate_attendance_entry(
            employee_id=input_data.employee_id,
            check_in_time=input_data.check_in_time,
            shift_start_time=input_data.shift_start_time,
            input_source=input_data.input_source
        )
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error in /validate_attendance: {e}")
        return {
            "success": False,
            "error_type": "AttendanceValidationError",
            "message": str(e),
            "tips": [
                "Ensure check-in and shift start times are valid ISO datetime strings.",
                "Check employee ID and input source."
            ]
        }

@app.post("/generate_report", response_model=Dict[str, Any])
async def generate_report_endpoint(input_data: ReportRequestInput):
    """
    Endpoint to generate attendance report.
    """
    try:
        result = await agent.generate_attendance_report(
            employee_id=input_data.employee_id,
            date_range=input_data.date_range,
            report_type=input_data.report_type
        )
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error in /generate_report: {e}")
        return {
            "success": False,
            "error_type": "ReportGenerationError",
            "message": str(e),
            "tips": [
                "Ensure employee ID and date range are valid.",
                "Check report type (daily, weekly, monthly)."
            ]
        }

@app.post("/detect_anomalies", response_model=Dict[str, Any])
async def detect_anomalies_endpoint(request: Request):
    """
    Endpoint to detect anomalies in attendance records.
    """
    try:
        data = await request.json()
        attendance_records = data.get("attendance_records", [])
        if not isinstance(attendance_records, list):
            raise HTTPException(status_code=400, detail="attendance_records must be a list.")
        result = await agent.detect_anomalies(attendance_records)
        return {"success": True, "anomalies": result}
    except Exception as e:
        logger.error(f"Error in /detect_anomalies: {e}")
        return {
            "success": False,
            "error_type": "AnomalyDetectionError",
            "message": str(e),
            "tips": [
                "Ensure attendance_records is a list of attendance record dicts."
            ]
        }

@app.post("/send_notification", response_model=Dict[str, Any])
async def send_notification_endpoint(input_data: NotificationInput):
    """
    Endpoint to send notification to user or HR.
    """
    try:
        result = await agent.send_notification(
            recipient=input_data.recipient,
            message=input_data.message,
            notification_type=input_data.notification_type
        )
        return {"success": result.get("success", False), "result": result}
    except Exception as e:
        logger.error(f"Error in /send_notification: {e}")
        return {
            "success": False,
            "error_type": "NotificationError",
            "message": str(e),
            "tips": [
                "Check recipient, message, and notification_type fields."
            ]
        }

@app.post("/authenticate_user", response_model=Dict[str, Any])
async def authenticate_user_endpoint(input_data: AuthInput):
    """
    Endpoint to authenticate user via SSO and 2FA.
    """
    try:
        result = await agent.authenticate_user(input_data.user_credentials)
        return {"success": result.get("authenticated", False), "result": result}
    except Exception as e:
        logger.error(f"Error in /authenticate_user: {e}")
        return {
            "success": False,
            "error_type": "AuthenticationError",
            "message": str(e),
            "tips": [
                "Ensure user_credentials contains username and 2fa_code."
            ]
        }

# Custom handler for malformed JSON
@app.middleware("http")
async def catch_malformed_json(request: Request, call_next):
    if request.method in ("POST", "PUT", "PATCH"):
        try:
            if request.headers.get("content-type", "").startswith("application/json"):
                await request.json()
        except Exception as e:
            logger.error(f"Malformed JSON: {e}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "error_type": "MalformedJSON",
                    "message": "Malformed JSON in request body.",
                    "details": str(e),
                    "tips": [
                        "Check for missing or extra commas, brackets, or quotes.",
                        "Ensure the request body is valid JSON.",
                        "Use double quotes for keys and string values."
                    ]
                }
            )
    response = await call_next(request)
    return response

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Ecommerce Attendance Tracker Agent API server...")
    uvicorn.run("agent:app", host="0.0.0.0", port=8000, reload=False)
