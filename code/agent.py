"""
Healthcare Employee Attendance Tracker - Generated Agent Implementation
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AgentConfig:
    """Agent configuration"""
    llm_provider: str = "openai"
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 2000
    api_key: Optional[str] = None

class HealthcareEmployeeAttendanceTrackerAgent:
    """Healthcare Employee Attendance Tracker - healthcare agent"""
    
    def __init__(self):
        self.config = self._load_config()
        self.llm_client = self._initialize_llm_client()
    
    def _load_config(self) -> AgentConfig:
        """Load agent configuration"""
        return AgentConfig(
            llm_provider=os.getenv("LLM_PROVIDER", "openai"),
            model=os.getenv("LLM_MODEL", "gpt-4o"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000")),
            api_key=os.getenv("OPENAI_API_KEY")
        )
    
    def _initialize_llm_client(self):
        """Initialize LLM client"""
        if self.config.llm_provider == "openai":
            from openai import AsyncOpenAI
            return AsyncOpenAI(api_key=self.config.api_key)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config.llm_provider}")
    
    async def process_message(self, message: str) -> str:
        """Process user message and generate response"""
        try:
            system_prompt = """You are a professional healthcare agent. {llm_configuration.get('system_prompt', 'Provide helpful assistance.')}"""
            
            response = await self.llm_client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "I apologize, but I encountered an error processing your request. Please try again."
    
    async def run(self):
        """Main agent loop"""
        print(f"{self.__class__.__name__} is running...")
        print("Type 'quit' to exit")
        
        while True:
            try:
                user_input = input("\\nYou: ")
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("Goodbye!")
                    break
                
                response = await self.process_message(user_input)
                print(f"Agent: {response}")
                
            except KeyboardInterrupt:
                print("\\nGoodbye!")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")

if __name__ == "__main__":
    agent = HealthcareEmployeeAttendanceTrackerAgent()
    asyncio.run(agent.run())
'''
    
    def _create_fallback_config_code(self, design) -> str:
        """Create fallback config code"""
        return f'''"""
Configuration management for Healthcare Employee Attendance Tracker
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration management"""
    
    def __init__(self):
        self.llm_provider = os.getenv("LLM_PROVIDER", "openai")
        self.llm_model = os.getenv("LLM_MODEL", "gpt-4o")
        self.llm_temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.llm_max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2000"))
        
        # API Keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        
        # Domain-specific config
        self.domain = "healthcare"
        self.personality = "professional"
        self.modality_type = "text"
        
        # Validate required API keys
        self._validate_api_keys()
    
    def _validate_api_keys(self):
        """Validate that required API keys are present"""
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")
        elif self.llm_provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")
        elif self.llm_provider == "google" and not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY is required")