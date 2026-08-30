from __future__ import annotations

import socket

import psutil

from .models import InterfaceInfo


def list_interfaces() -> list[InterfaceInfo]:
    result: list[InterfaceInfo] = []
    for name, addrs in psutil.net_if_addrs().items():
        ipv4 = None
        ipv6 = None
        for addr in addrs:
            if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                ipv4 = ipv4 or addr.address
            elif addr.family == socket.AF_INET6 and not addr.address.startswith("::1"):
                ipv6 = ipv6 or addr.address.split("%", 1)[0]
        result.append(InterfaceInfo(name=name, ipv4=ipv4, ipv6=ipv6))
    return sorted(result, key=lambda i: (i.ipv4 is None, i.name.lower()))
