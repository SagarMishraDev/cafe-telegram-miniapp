from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    BOT_TOKEN: str = ""
    WEBAPP_URL: str = "http://localhost:5173"
    DATABASE_URL: str = ""
    JWT_SECRET: str = "dev-secret-change-in-prod"
    DEV_AUTH: int = 1
    GROUP_CHAT_ID: str = ""
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,*"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    class Config:
        env_file = ".env"
settings = Settings()
def get_db_url():
    if settings.DATABASE_URL:
        u=settings.DATABASE_URL
        if u.startswith("postgres://"): u=u.replace("postgres://","postgresql://",1)
        return u
    return "sqlite:///./cafe.db"
