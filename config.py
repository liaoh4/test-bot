from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    TWILIO_ACCOUNT_SID: str
    TWILIO_API_KEY: str
    TWILIO_API_SECRET: str
    TWILIO_CALLER_NUMBER: str
    TARGET_PHONE_NUMBER: str
    DEEPGRAM_API_KEY: str
    ELEVENLABS_API_KEY: str
    ELEVENLABS_VOICE_ID: str
    DEEPSEEK_API_KEY: str
    WEBHOOK_BASE_URL: str = ""
    USE_NGROK: bool = True
    APP_PORT: int = 8001
    PATIENT_NAME: str = "Sarah Mitchell"
    PATIENT_DOB: str = "July 4th, 2000"


settings = Settings()
