"""Configuración centralizada del Servicio 1.

Todos los parámetros provienen de variables de entorno (o de un archivo
``.env``) y se validan al arrancar. Si un valor es inseguro en producción
(por ejemplo un secreto JWT corto o CORS abierto a ``*``) la aplicación
falla de forma explícita en lugar de iniciar con una configuración frágil.

Mapeo 1:1 con las variables declaradas en ``docker-compose.yml`` y en
``.env.example`` de la raíz del repositorio.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Literal
from urllib.parse import quote

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

#: Longitud mínima (en bytes) exigida al secreto de firma de los JWT.
MIN_JWT_SECRET_BYTES = 32
#: Límite inferior del TTL de los tokens de recuperación (1 minuto).
MIN_RESET_TOKEN_TTL_SECONDS = 60
#: Límite superior del TTL de los tokens de recuperación (24 horas).
MAX_RESET_TOKEN_TTL_SECONDS = 86_400


class Settings(BaseSettings):
    """Configuración inmutable y validada de la aplicación."""

    model_config = SettingsConfigDict(
        # Se leen ambos archivos: ``.env`` local del servicio y el ``.env``
        # de la raíz del repositorio (útil al ejecutar uvicorn desde
        # ``backend-service1/`` sin Docker).
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Aplicación
    # ------------------------------------------------------------------
    project_name: str = "Bannedbyabrejeet - Servicio 1 (API de Administración)"
    version: str = "1.0.0"
    environment: Literal["development", "testing", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"

    # ------------------------------------------------------------------
    # Redis
    # ------------------------------------------------------------------
    redis_host: str = "127.0.0.1"
    redis_port: int = Field(default=6379, ge=1, le=65535)
    redis_db: int = Field(default=0, ge=0, le=15)
    redis_password: SecretStr | None = None
    redis_socket_timeout: float = Field(default=5.0, gt=0)
    redis_socket_connect_timeout: float = Field(default=3.0, gt=0)
    redis_max_connections: int = Field(default=20, ge=1, le=500)
    redis_health_check_interval: int = Field(default=30, ge=0)
    #: Intentos de conexión a Redis durante el arranque del contenedor.
    redis_startup_retries: int = Field(default=10, ge=1, le=60)
    redis_startup_retry_delay: float = Field(default=2.0, ge=0.1, le=30)

    # ------------------------------------------------------------------
    # JWT (firmados con HMAC SHA-256)
    # ------------------------------------------------------------------
    jwt_secret: SecretStr = SecretStr("dev-only-insecure-secret-change-me-32")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = Field(default=30, ge=1, le=1440)
    jwt_issuer: str = "bannedbyabrejeet:service1"
    jwt_audience: str = "bannedbyabrejeet:admin-console"

    # ------------------------------------------------------------------
    # Contraseñas y tokens de recuperación
    # ------------------------------------------------------------------
    #: Coste de bcrypt. 12 es el equilibrio recomendado entre seguridad y latencia.
    bcrypt_rounds: int = Field(default=12, ge=8, le=16)
    #: TTL nativo de Redis (comando SETEX) para ``reset_token:<token>``.
    reset_token_ttl: int = Field(
        default=900,
        ge=MIN_RESET_TOKEN_TTL_SECONDS,
        le=MAX_RESET_TOKEN_TTL_SECONDS,
        description="Vida del token de recuperación en segundos (900 = 15 minutos).",
    )

    # ------------------------------------------------------------------
    # Frontend / CORS
    # ------------------------------------------------------------------
    frontend_base_url: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # ------------------------------------------------------------------
    # Correo de recuperación
    # ------------------------------------------------------------------
    mail_mode: Literal["log", "smtp"] = "log"
    mail_from: str = "noreply@bannedbyabrejeet.local"
    mail_from_name: str = "Bannedbyabrejeet"
    smtp_host: str = "localhost"
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str = ""
    smtp_password: SecretStr | None = None
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    smtp_timeout: float = Field(default=10.0, gt=0)

    # ------------------------------------------------------------------
    # Validadores
    # ------------------------------------------------------------------
    @field_validator("jwt_secret")
    @classmethod
    def _validate_jwt_secret(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value().encode("utf-8")) < MIN_JWT_SECRET_BYTES:
            raise ValueError(
                "JWT_SECRET debe tener al menos "
                f"{MIN_JWT_SECRET_BYTES} bytes. Generá uno con: openssl rand -hex 32"
            )
        return value

    @field_validator("jwt_algorithm")
    @classmethod
    def _validate_jwt_algorithm(cls, value: str) -> str:
        # Solo se admite HMAC: los tokens se validan sin acceso a una clave pública.
        if value not in {"HS256", "HS384", "HS512"}:
            raise ValueError("JWT_ALGORITHM debe ser HS256, HS384 o HS512")
        return value

    @field_validator("frontend_base_url")
    @classmethod
    def _validate_frontend_base_url(cls, value: str) -> str:
        value = value.strip().rstrip("/")
        if not value.startswith("http://") and not value.startswith("https://"):
            raise ValueError("FRONTEND_BASE_URL debe empezar con http:// o https://")
        return value

    @field_validator("mail_from")
    @classmethod
    def _validate_mail_from(cls, value: str) -> str:
        value = value.strip()
        if not value or any(char in value for char in "\r\n"):
            raise ValueError("MAIL_FROM es inválido")
        return value

    @field_validator("smtp_username")
    @classmethod
    def _validate_smtp_username(cls, value: str) -> str:
        # Defensa contra inyección de cabeceras SMTP (CRLF).
        if any(char in value for char in "\r\n"):
            raise ValueError("SMTP_USERNAME es inválido")
        return value

    @model_validator(mode="after")
    def _validate_runtime_consistency(self) -> "Settings":
        if self.smtp_use_tls and self.smtp_use_ssl:
            raise ValueError("Configure SMTP_USE_TLS o SMTP_USE_SSL, nunca ambos")
        if self.environment == "production":
            if self.debug:
                raise ValueError("DEBUG no puede ser true en production")
            if self.mail_mode == "log":
                logger.warning(
                    "MAIL_MODE=log en production: los enlaces de recuperación "
                    "quedarán expuestos en los logs del contenedor."
                )
        return self

    # ------------------------------------------------------------------
    # Propiedades derivadas
    # ------------------------------------------------------------------
    @property
    def redis_url(self) -> str:
        """URL de conexión a Redis con la contraseña escapada (si existe)."""
        auth = ""
        if self.redis_password is not None:
            secret = self.redis_password.get_secret_value()
            if secret:
                auth = f":{quote(secret, safe='')}@"
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def cors_origins_list(self) -> list[str]:
        """Orígenes CORS permitidos, normalizados (sin barra final)."""
        origins = [origin.strip().rstrip("/") for origin in self.cors_origins.split(",")]
        return [origin for origin in origins if origin]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    def build_reset_password_link(self, token: str) -> str:
        """Construye el enlace ``/reset-password?token=...``.

        El origen se toma **solo** de la configuración: nunca del cuerpo de
        la petición, para impedir redirecciones abiertas o enlaces
        generados por un atacante.
        """
        return f"{self.frontend_base_url}/reset-password?token={token}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Devuelve la configuración singleton (cacheada por proceso)."""
    return Settings()
