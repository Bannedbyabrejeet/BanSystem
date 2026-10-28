"""Utilidades de validación y normalización de direcciones IP y subredes.

La lista blanca acepta tanto direcciones sueltas (``192.168.1.10``) como
redes en notación CIDR (``10.0.0.0/8``). Se normalizan con ``ipaddress``
para que una misma entrada no pueda guardarse de dos formas distintas
(por ejemplo ``10.1.2.3/8`` y ``10.0.0.0/8``).

Las entradas locales protegidas son inmutables por contrato (US-08).
"""

from __future__ import annotations

from ipaddress import ip_address, ip_network
from typing import Final

#: Entradas que siempre deben existir en ``config:whitelist``.
PROTECTED_WHITELIST_ENTRIES: Final[tuple[str, ...]] = ("127.0.0.1", "::1")

#: Versiones normalizadas de las entradas protegidas.
_PROTECTED_ADDRESSES: Final[frozenset] = frozenset(
    ip_address(entry) for entry in PROTECTED_WHITELIST_ENTRIES
)


def normalize_ip_or_network(value: str) -> str:
    """Normaliza una IP o subred y devuelve su representación canónica.

    Raises:
        ValueError: el texto no es una dirección IPv4/IPv6 ni una red CIDR
            válida, o el prefijo está fuera de rango.
    """
    text = (value or "").strip()
    if not text:
        raise ValueError("La dirección está vacía.")

    if "/" in text:
        # ``strict=False`` permite escribir 10.1.2.3/8 y lo normaliza a
        # 10.0.0.0/8, que es lo que se persiste en Redis.
        return str(ip_network(text, strict=False))

    return str(ip_address(text))


def is_protected_whitelist_entry(value: str) -> bool:
    """``True`` si la entrada representa una de las IPs locales protegidas.

    Se comparan tanto direcciones sueltas como redes de un único host
    (``127.0.0.1/32`` o ``::1/128``) para que no se pueda sortear la
    protección cambiando la notación.
    """
    try:
        network = ip_network(normalize_ip_or_network(value), strict=False)
    except ValueError:
        return False

    return (
        network.num_addresses == 1
        and network.network_address in _PROTECTED_ADDRESSES
    )
