"""Configuración del Servicio 2 basada en variables de entorno.

Reutiliza el mismo ``.env`` de la raíz del repositorio que el Servicio 1 para
compartir ``REDIS_*``. Las variables propias del motor de logs llevan el
prefijo ``SSH_`` / ``LOG_`` para no chocar con la API de administración.
"""

from __future__ import annotations

from functools import lru_cache
from urllib.parse import quote

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración inmutable del motor de seguridad."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    project_name: str = "Bannedbyabrejeet - Servicio 2 (Motor de Seguridad)"
    version: str = "1.0.0"
    environment: str = "development"
    log_level: str = "INFO"

    # ------------------------------------------------------------------
    # Redis (mismas claves que escribe el Servicio 1)
    # ------------------------------------------------------------------
    redis_host: str = "127.0.0.1"
    redis_port: int = Field(default=6379, ge=1, le=65535)
    redis_db: int = Field(default=0, ge=0, le=15)
    redis_password: SecretStr | None = None
    redis_socket_timeout: float = Field(default=5.0, gt=0)
    redis_socket_connect_timeout: float = Field(default=3.0, gt=0)
    redis_health_check_interval: int = Field(default=30, ge=0)
    redis_startup_retries: int = Field(default=10, ge=1, le=60)
    redis_startup_retry_delay: float = Field(default=2.0, ge=0.1, le=30)

    # ------------------------------------------------------------------
    # Lector de logs
    # ------------------------------------------------------------------
    #: Ruta del auth log. En Debian/Ubuntu: /var/log/auth.log; en RHEL: /var/log/secure.
    ssh_log_path: str = "/var/log/auth.log"
    #: ``False`` arranca al final del archivo (solo eventos nuevos, como ``tail -f``).
    log_read_from_start: bool = False
    #: Espera entre sondeos del archivo cuando no hay líneas nuevas.
    log_poll_interval: float = Field(default=0.5, gt=0, le=60)
    log_encoding: str = "utf-8"

    # ------------------------------------------------------------------
    # Flask (healthcheck del proceso)
    # ------------------------------------------------------------------
    api_host: str = "127.0.0.1"
    api_port: int = Field(default=5000, ge=1, le=65535)

    @property
    def redis_url(self) -> str:
        """URL de Redis con la contraseña escapada."""
        auth = ""
        if self.redis_password is not None:
            secret = self.redis_password.get_secret_value()
            if secret:
                auth = f":{quote(secret, safe='')}@"
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Devuelve la configuración singleton del proceso."""
    return Settings()
