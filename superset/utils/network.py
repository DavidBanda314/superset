# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import ipaddress
import platform
import socket
import subprocess
from typing import Any

import requests
from urllib3.connection import HTTPConnection, HTTPSConnection
from urllib3.connectionpool import HTTPConnectionPool, HTTPSConnectionPool
from urllib3.exceptions import ConnectTimeoutError, NewConnectionError
from urllib3.util.connection import create_connection

# Networks that must never be reached via user-supplied hostnames.
# Includes loopback, RFC-1918 private ranges, link-local (covers cloud
# metadata endpoints such as 169.254.169.254), shared address space
# (RFC 6598, 100.64.0.0/10), multicast (ip.is_global returns True for
# multicast addresses in Python, so explicit blocking is required), and
# IPv6 equivalents.
_SSRF_UNSAFE_NETWORKS = (
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("224.0.0.0/4"),  # IPv4 multicast — is_global is True in Python
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("ff00::/8"),  # IPv6 multicast
)

PORT_TIMEOUT = 5
PING_TIMEOUT = 5


def is_safe_ip(address: str) -> bool:
    """
    Return True if ``address`` is a public, globally-routable IP address.
    """
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    # Unwrap IPv4-mapped IPv6 addresses (e.g. ::ffff:127.0.0.1) so they
    # are checked against the IPv4 unsafe networks rather than bypassing.
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_global and not any(ip in net for net in _SSRF_UNSAFE_NETWORKS)


def is_safe_host(host: str) -> bool:
    """
    Return True if ``host`` resolves exclusively to public, globally-routable
    IP addresses.

    Returns False if any resolved address falls within a private, loopback,
    link-local, or otherwise non-routable range.  An unresolvable host also
    returns False.

    This is a point-in-time check: the name is resolved again when a
    connection is opened, so a hostname whose records change between the two
    resolutions (DNS rebinding) can still connect to an unsafe address.  Use
    :func:`safe_requests_session` for the request itself so that the address
    the socket actually connects to is the one that gets vetted.
    """
    try:
        results = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    if not results:
        return False
    return all(is_safe_ip(str(sockaddr[0])) for _, _, _, _, sockaddr in results)


def _resolve_safe_addresses(host: str, port: int | None) -> list[str]:
    """
    Resolve ``host`` and return only the addresses that are safe to connect to.
    """
    return [
        str(sockaddr[0])
        for _, _, _, _, sockaddr in socket.getaddrinfo(host, port)
        if is_safe_ip(str(sockaddr[0]))
    ]


class SafeHostHTTPConnection(HTTPConnection):
    """
    HTTP connection that only opens sockets to globally-routable addresses.

    The address the socket connects to is the address that was vetted, which
    closes the DNS rebinding window left open by validating a hostname before
    handing that same hostname to the HTTP client.  ``host`` is left untouched
    so the ``Host`` header and TLS SNI still carry the hostname.
    """

    def _new_conn(self) -> socket.socket:
        extra_kw: dict[str, Any] = {}
        if self.source_address:
            extra_kw["source_address"] = self.source_address
        if self.socket_options:
            extra_kw["socket_options"] = self.socket_options

        host = self._dns_host.rstrip(".")
        try:
            addresses = _resolve_safe_addresses(host, self.port)
        except socket.gaierror as ex:
            raise NewConnectionError(self, f"Failed to resolve {host}: {ex}") from ex
        if not addresses:
            raise NewConnectionError(
                self,
                f"Refusing to connect to {host}: it does not resolve to a "
                "public, globally-routable address.",
            )

        error: OSError | None = None
        for address in addresses:
            try:
                # A literal address is passed on, so no further name
                # resolution happens here.
                return create_connection((address, self.port), self.timeout, **extra_kw)
            except socket.timeout as ex:
                raise ConnectTimeoutError(
                    self,
                    f"Connection to {host} timed out. (connect timeout={self.timeout})",
                ) from ex
            except OSError as ex:
                error = ex
        raise NewConnectionError(self, f"Failed to establish a new connection: {error}")


class SafeHostHTTPSConnection(HTTPSConnection):
    """HTTPS counterpart of :class:`SafeHostHTTPConnection`."""

    _new_conn = SafeHostHTTPConnection._new_conn  # noqa: SLF001


class SafeHostHTTPConnectionPool(HTTPConnectionPool):
    ConnectionCls = SafeHostHTTPConnection


class SafeHostHTTPSConnectionPool(HTTPSConnectionPool):
    ConnectionCls = SafeHostHTTPSConnection


class SafeHostHTTPAdapter(requests.adapters.HTTPAdapter):
    """
    ``requests`` adapter that refuses to connect to non-global addresses.
    """

    def init_poolmanager(self, *args: Any, **kwargs: Any) -> None:
        super().init_poolmanager(*args, **kwargs)
        self.poolmanager.pool_classes_by_scheme = {
            "http": SafeHostHTTPConnectionPool,
            "https": SafeHostHTTPSConnectionPool,
        }


def safe_requests_session() -> requests.Session:
    """
    Build a ``requests`` session whose sockets can only reach public,
    globally-routable addresses.
    """
    session = requests.Session()
    adapter = SafeHostHTTPAdapter()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def is_port_open(host: str, port: int) -> bool:
    """
    Test if a given port in a host is open.
    """
    # pylint: disable=invalid-name
    for res in socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM):
        af, _, _, _, sockaddr = res
        s = socket.socket(af, socket.SOCK_STREAM)
        try:
            s.settimeout(PORT_TIMEOUT)
            s.connect(sockaddr)
            s.shutdown(socket.SHUT_RDWR)
            return True
        except OSError as _:
            continue
        finally:
            s.close()
    return False


def is_hostname_valid(host: str) -> bool:
    """
    Test if a given hostname can be resolved.
    """
    try:
        socket.getaddrinfo(host, None)
        return True
    except socket.gaierror:
        return False


def is_host_up(host: str) -> bool:
    """
    Ping a host to see if it's up.

    Note that if we don't get a response the host might still be up,
    since many firewalls block ICMP packets.
    """
    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = ["ping", param, "1", host]
    try:
        output = subprocess.call(command, timeout=PING_TIMEOUT)  # noqa: S603
    except subprocess.TimeoutExpired:
        return False

    return output == 0
