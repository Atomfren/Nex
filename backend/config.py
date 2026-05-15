"""Backend конфигурация."""

from loguru import logger

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Конфигурация backend сервиса."""
    
    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False
    
    # Application
    app_name: str = "NexoraLauncher Backend"
    app_version: str = "0.1.0"
    
    # Paths
    data_dir: str = ""
    config_dir: str = ""
    instances_dir: str = ""
    minecraft_dir: str = ""
    
    # AI
    ai_model_path: str = ""
    ai_n_ctx: int = 4096
    ai_n_threads: int = 4
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_prefix = "QUANTUMLAUNCHER_BACKEND_"
        env_file = ".env"
        case_sensitive = False


try:
    settings = Settings()
except Exception as e:
    logger.warning(f"Failed to load settings from env: {e}")
    settings = Settings()
