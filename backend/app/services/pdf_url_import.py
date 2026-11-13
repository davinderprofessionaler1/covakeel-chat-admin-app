"""Download an admin-supplied public HTTPS PDF for the existing indexing flow."""

import asyncio
import base64
import binascii
import ipaddress
import json
import re
import socket
import ssl
from pathlib import Path
from urllib.parse import unquote, urlsplit

import httpx

from app.services.admin_service import MAX_PDF_BYTES


CBIC_HOST = "taxinformation.cbic.gov.in"
CBIC_VIEWER = re.compile(r"^/view-pdf/([1-9][0-9]{0,11})/(ENG|HINDI)/(Notifications|Circulars)/?$", re.IGNORECASE)
CBIC_INTERMEDIATE = Path(__file__).resolve().parents[1] / "certs" / "sectigo-public-server-auth-ca-ov-r36.pem"


def parse_pdf_url(url: str) -> tuple[str, str]:
    url = url.strip()
    if re.search(r"[\x00-\x20\x7f]", url):
        raise ValueError("Enter a valid HTTPS PDF URL")
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Enter a valid HTTPS PDF URL") from exc
    host = parsed.hostname
    if (parsed.scheme != "https" or not host or parsed.username or parsed.password
            or port not in (None, 443) or parsed.fragment):
        raise ValueError("Enter a direct HTTPS PDF URL without credentials or a custom port")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValueError("Use a public website hostname, not an IP address")
    if host.lower() in {"localhost"} or host.lower().endswith((".localhost", ".local")):
        raise ValueError("Use a public website hostname")
    viewer = CBIC_VIEWER.fullmatch(parsed.path) if host.lower() == CBIC_HOST and not parsed.query else None
    if viewer:
        kind = "Notification" if viewer.group(3).lower() == "notifications" else "Circular"
        filename = f"CBIC_{kind}_{viewer.group(1)}_{viewer.group(2).upper()}.pdf"
    else:
        raw_name = unquote(parsed.path.rsplit("/", 1)[-1])
        if not raw_name.lower().endswith(".pdf"):
            raise ValueError("Link directly to a .pdf file or use a CBIC notification viewer link")
        filename = re.sub(r"[^A-Za-z0-9._-]", "_", raw_name).lstrip(".")[:160]
        if not filename.lower().endswith(".pdf") or filename == ".pdf":
            raise ValueError("The PDF link needs a valid filename")
    return url, filename


async def _verify_public_host(host: str) -> None:
    try:
        addresses = await asyncio.to_thread(socket.getaddrinfo, host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError("Could not resolve the PDF website") from exc
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError("PDF links must point to a public website")


async def download_pdf(url: str) -> tuple[str, bytes]:
    url, filename = parse_pdf_url(url)
    parsed = urlsplit(url)
    await _verify_public_host(parsed.hostname)
    viewer = CBIC_VIEWER.fullmatch(parsed.path) if parsed.hostname.lower() == CBIC_HOST and not parsed.query else None
    api_kind = "notification" if viewer and viewer.group(3).lower() == "notifications" else "circular"
    request_url = (f"https://{CBIC_HOST}/api/cbic-{api_kind}-msts/download/"
                   f"{viewer.group(1)}/{viewer.group(2).upper()}") if viewer else url
    verification = True
    if parsed.hostname.lower() == CBIC_HOST:
        # CBIC currently omits this Sectigo intermediate from its TLS handshake.
        # Add the CA certificate to normal system trust; never disable verification.
        verification = ssl.create_default_context()
        verification.load_verify_locations(str(CBIC_INTERMEDIATE))
    max_response_bytes = (MAX_PDF_BYTES + 2) // 3 * 4 + 4096 if viewer else MAX_PDF_BYTES
    try:
        async with asyncio.timeout(40):
            async with httpx.AsyncClient(follow_redirects=False, trust_env=False,
                                         verify=verification, timeout=httpx.Timeout(20.0, connect=10.0)) as client:
                async with client.stream("GET", request_url) as response:
                    if 300 <= response.status_code < 400:
                        raise ValueError("This link redirects. Paste the final direct PDF URL")
                    response.raise_for_status()
                    length = response.headers.get("content-length", "0")
                    if length.isdigit() and int(length) > max_response_bytes:
                        raise ValueError("PDF must be 20 MB or smaller")
                    data = bytearray()
                    async for chunk in response.aiter_bytes():
                        data.extend(chunk)
                        if len(data) > max_response_bytes:
                            raise ValueError("PDF must be 20 MB or smaller")
    except TimeoutError as exc:
        raise ValueError("PDF download timed out") from exc
    except httpx.HTTPError as exc:
        raise ValueError("Could not download the PDF from that link") from exc
    if viewer:
        try:
            payload = json.loads(data)
            data = base64.b64decode(payload["data"], validate=True)
        except (ValueError, KeyError, TypeError, binascii.Error) as exc:
            raise ValueError("CBIC did not return a usable PDF") from exc
    if len(data) > MAX_PDF_BYTES:
        raise ValueError("PDF must be 20 MB or smaller")
    if not data.startswith(b"%PDF-"):
        raise ValueError("The link did not return a valid PDF")
    return filename, bytes(data)
