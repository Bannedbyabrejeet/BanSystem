"""Servicio de correo para los enlaces de recuperación de contraseña.

Dos modos, seleccionados con ``MAIL_MODE``:

* ``log`` (por defecto, solo desarrollo): escribe el enlace completo en el
  log del contenedor. Permite demostrar el flujo sin depender de un SMTP.
* ``smtp``: entrega el mensaje con :mod:`smtplib`.

En ambos casos el envío se ejecuta en un hilo aparte para no bloquear el
event loop de FastAPI.
"""

from __future__ import annotations

import logging
import smtplib
import ssl
from email.header import Header
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid
from urllib.parse import quote

import anyio

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

SUBJECT_TEMPLATE = "{prefix}Restablecer contraseña de administrador"
BODY_TEMPLATE = """Hola {username},

Recibimos una solicitud para restablecer la contraseña del administrador de
Bannedbyabrejeet.

Usá este enlace dentro de los próximos {minutes} minutos:

{link}

Si no solicitaste el cambio, ignorá este mensaje: la contraseña actual sigue
siendo válida. Por seguridad, el enlace deja de funcionar después de su
primer uso.

--
Bannedbyabrejeet · Servicio de seguridad SSH
"""


class MailDeliveryError(RuntimeError):
    """No se pudo entregar el correo (solo en modo ``smtp``)."""


class MailService:
    """Construye y entrega el correo de recuperación."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    async def send_password_reset(self, *, to_email: str, username: str, token: str) -> str:
        """Envía el enlace de recuperación y devuelve la URL generada.

        Returns:
            El enlace ``/reset-password?token=...`` construido a partir de
            ``FRONTEND_BASE_URL`` (nunca a partir de la petición).
        """
        link = self.build_reset_link(token)
        subject = SUBJECT_TEMPLATE.format(prefix=f"[{self.settings.mail_from_name}] ")
        body = BODY_TEMPLATE.format(
            username=username,
            minutes=max(1, round(self.settings.reset_token_ttl / 60)),
            link=link,
        )

        if self.settings.mail_mode == "smtp":
            await anyio.to_thread.run_sync(self._send_via_smtp, to_email, subject, body)
        else:
            logger.warning(
                "MAIL_MODE=log: enlace de recuperación para %s (vigente %ss): %s",
                to_email,
                self.settings.reset_token_ttl,
                link,
            )
        return link

    def build_reset_link(self, token: str) -> str:
        """Construye la URL absoluta del enlace de recuperación."""
        return self.settings.build_reset_password_link(quote(token, safe=""))

    # ------------------------------------------------------------------
    # Transporte SMTP
    # ------------------------------------------------------------------
    def _send_via_smtp(self, to_email: str, subject: str, body: str) -> None:
        """Entrega el mensaje usando el servidor SMTP configurado."""
        message = EmailMessage()
        message["Subject"] = Header(subject, "utf-8")
        message["From"] = formataddr(
            (str(Header(self.settings.mail_from_name, "utf-8")), self.settings.mail_from)
        )
        message["To"] = to_email
        message["Date"] = formatdate(localtime=True)
        message["Message-ID"] = make_msgid(domain="bannedbyabrejeet.local")
        message.set_content(body, charset="utf-8")

        timeout = self.settings.smtp_timeout
        username = self.settings.smtp_username
        password = (
            self.settings.smtp_password.get_secret_value()
            if self.settings.smtp_password is not None
            else ""
        )

        try:
            if self.settings.smtp_use_ssl:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(
                    self.settings.smtp_host, self.settings.smtp_port, timeout=timeout, context=context
                ) as server:
                    self._smtp_auth_and_send(server, username, password, to_email, message)
            else:
                with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=timeout) as server:
                    server.ehlo()
                    if self.settings.smtp_use_tls:
                        server.starttls(context=ssl.create_default_context())
                        server.ehlo()
                    self._smtp_auth_and_send(server, username, password, to_email, message)
        except (smtplib.SMTPException, OSError) as exc:
            logger.error("Fallo al enviar el correo de recuperación: %s", exc)
            raise MailDeliveryError(str(exc)) from exc

        logger.info("Correo de recuperación entregado a %s", to_email)

    @staticmethod
    def _smtp_auth_and_send(
        server: smtplib.SMTP,
        username: str,
        password: str,
        to_email: str,
        message: EmailMessage,
    ) -> None:
        """Autentica (si corresponde) y envía el mensaje."""
        if username:
            server.login(username, password)
        server.send_message(message)


def get_mail_service() -> MailService:
    """Dependencia de FastAPI: instancia del servicio de correo."""
    return MailService()
