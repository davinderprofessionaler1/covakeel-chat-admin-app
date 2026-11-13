import asyncio
import socket
import unittest
from unittest.mock import AsyncMock, patch

from app.services.pdf_url_import import _verify_public_host, parse_pdf_url


class PdfUrlValidationTests(unittest.TestCase):
    def test_accepts_direct_public_pdf_url_with_query(self):
        url = "https://www.gstcouncil.gov.in/sites/default/files/2024-02/consti-amend-act.pdf?download=1"
        self.assertEqual(parse_pdf_url(url), (url, "consti-amend-act.pdf"))

    def test_accepts_cbic_notification_viewer_link(self):
        url = "https://taxinformation.cbic.gov.in/view-pdf/1000874/ENG/Notifications"
        self.assertEqual(parse_pdf_url(url), (url, "CBIC_Notification_1000874_ENG.pdf"))

    def test_accepts_cbic_circular_viewer_link(self):
        url = "https://taxinformation.cbic.gov.in/view-pdf/1003065/ENG/Circulars"
        self.assertEqual(parse_pdf_url(url), (url, "CBIC_Circular_1003065_ENG.pdf"))

    def test_rejects_internal_and_non_pdf_links(self):
        for url in (
            "http://www.gstcouncil.gov.in/document.pdf",
            "https://127.0.0.1/document.pdf",
            "https://localhost/document.pdf",
            "https://internal.local/document.pdf",
            "https://user:password@example.com/document.pdf",
            "https://example.com:8443/document.pdf",
            "https://example.com/document.html",
            "https://example.com/view-pdf/1000874/ENG/Notifications",
            "https://taxinformation.cbic.gov.in/view-pdf/1000874/ENG/Unknown",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                parse_pdf_url(url)

    def test_rejects_private_dns_results(self):
        address = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 443))]
        with patch("app.services.pdf_url_import.asyncio.to_thread", new_callable=AsyncMock, return_value=address):
            with self.assertRaisesRegex(ValueError, "public website"):
                asyncio.run(_verify_public_host("example.com"))
