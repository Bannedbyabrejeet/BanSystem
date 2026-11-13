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
    # JWT compartido con el Servicio 1 (Frontend B consume telemetría)
    # ------------------------------------------------------------------
    jwt_secret: SecretStr = SecretStr("dev-only-insecure-secret-change-me-32")
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "bannedbyabrejeet:service1"
    jwt_audience: str = "bannedbyabrejeet:admin-console"

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
    #: Cantidad máxima de eventos SSH retenidos en Redis para el visor.
    ssh_events_limit: int = Field(default=2_000, ge=100, le=50_000)

    # ------------------------------------------------------------------
    # UFW (Issue #8)
    # ------------------------------------------------------------------
    #: ``True`` ejecuta UFW en modo simulación: registra el comando pero no
    #: modifica el firewall. Útil para desarrollo y para las pruebas manuales.
    ufw_dry_run: bool = False
    #: Binario de UFW. En Debian/Ubuntu suele ser ``/usr/sbin/ufw``.
    ufw_binary: str = "ufw"
    #: Ejecutar mediante ``sudo -n`` (sin prompt interactivo). Si el proceso
    #: corre como root puede dejarse en ``True``; sudo no pide contraseña.
    ufw_use_sudo: bool = True
    #: Puerto SSH que se bloquea con la regla ``deny from <IP> to any port``.
    ufw_ssh_port: int = Field(default=22, ge=1, le=65535)
    #: Tiempo máximo de espera de cada comando UFW.
    ufw_command_timeout: float = Field(default=10.0, gt=0, le=120)

    # ------------------------------------------------------------------
    # Baneos: expiración y desbaneo manual (Issue #8)
    # ------------------------------------------------------------------
    #: Cada cuántos segundos el motor revisa baneos vencidos en Redis.
    ban_maintenance_interval: float = Field(default=5.0, gt=0, le=300)
    #: Stream del contrato de desbaneo manual (Issue #2).
    unban_stream: str = "security:events:unban"
    #: Consumer group definido en ``docs/contrato-desbaneo.yaml``.
    unban_consumer_group: str = "ufw_workers"
    #: Nombre del consumidor. Vacío = ``service2-<host>-<pid>``.
    unban_consumer_name: str = ""
    #: ``XREADGROUP BLOCK`` en milisegundos.
    unban_block_ms: int = Field(default=1000, ge=0, le=60_000)
    #: Cantidad máxima de mensajes leídos por iteración.
    unban_batch_size: int = Field(default=10, ge=1, le=100)
    #: Tiempo mínimo (ms) que un mensaje fallido espera antes de reintentarse.
    unban_retry_min_idle_ms: int = Field(default=5_000, ge=0, le=600_000)

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
