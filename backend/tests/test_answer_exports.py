"""Cited PDFs and answer exports stay tied to the requesting chat."""

import asyncio
from datetime import datetime, timezone
from io import BytesIO
from unicodedata import normalize
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch
from xml.etree import ElementTree
from zipfile import ZipFile

from bson import ObjectId
from httpx import ASGITransport, AsyncClient
import fitz

from app.core.security import get_current_user
from app.main import app
from app.services.answer_export import export_docx, export_pdf
from app.services.message_service import get_question_for_answer


class AnswerExportTests(unittest.TestCase):
    @staticmethod
    async def get(path):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.get(path)

    def test_pdf_and_docx_contain_answer_and_cited_source(self):
        source = SimpleNamespace(filename="law.pdf", metadata={
            "citation_id": "1", "title": "Official law", "page": 4,
            "source_url": "https://example.gov.in/law.pdf",
        })
        answer = "**Direct answer**\nA rule applies [1].\n\nਪੰਜਾਬੀ explanation."
        pdf = fitz.open(stream=export_pdf(answer, [source], question="What does the rule say?",
            generated_at=datetime(2026, 11, 13, 6, 0, tzinfo=timezone.utc)), filetype="pdf")
        self.assertIn("Query", pdf[0].get_text())
        self.assertIn("What does the rule say?", pdf[0].get_text())
        self.assertIn("Response", pdf[0].get_text())
        self.assertIn("Downloaded 13 Nov 2026", pdf[0].get_text())
        self.assertIn("1 / 1", pdf[0].get_text())
        self.assertIn("A rule applies [1]", pdf[0].get_text())
        self.assertIn("Official law", normalize("NFKC", pdf[0].get_text()))
        self.assertIn("ਪੰਜਾਬੀ", pdf[0].get_text())
        self.assertGreaterEqual(sum(link.get("uri") == "https://example.gov.in/law.pdf" for link in pdf[0].get_links()), 2)
        with ZipFile(BytesIO(export_docx(answer, [source]))) as archive:
            document = ElementTree.fromstring(archive.read("word/document.xml"))
        text = "".join(document.itertext())
        self.assertIn("A rule applies [1]", text)
        self.assertIn("Official law", text)
        self.assertIn("ਪੰਜਾਬੀ", text)

    def test_long_pdf_repeats_header_and_footer_on_every_page(self):
        answer = "**Detailed explanation**\n" + "A cited example [1]. " * 900
        pdf = fitz.open(stream=export_pdf(answer, [], question="Example?"), filetype="pdf")
        self.assertGreater(len(pdf), 1)
        for page_number, page in enumerate(pdf, 1):
            content = page.get_text()
            self.assertIn("CoVakeel", content)
            self.assertIn(f"{page_number} / {len(pdf)}", content)

    def test_pdf_uses_the_user_turn_before_the_saved_answer(self):
        message = SimpleNamespace(conversationId=ObjectId(), createdAt=datetime(2026, 11, 13, 6, 0))
        question = {"text": "Which provision changed?"}
        db = {"messages": SimpleNamespace(find_one=AsyncMock(return_value=question))}
        with patch("app.services.message_service.get_db", return_value=db):
            self.assertEqual(asyncio.run(get_question_for_answer(message)), question["text"])
        query = db["messages"].find_one.await_args
        self.assertEqual(query.args[0]["conversationId"], message.conversationId)
        self.assertEqual(query.args[0]["createdAt"], {"$lte": message.createdAt})

    def test_other_users_cannot_export_an_answer(self):
        owner = ObjectId()
        other = ObjectId()
        async def current_user():
            return SimpleNamespace(_id=other)
        app.dependency_overrides[get_current_user] = current_user
        try:
            with patch("app.controllers.message_controller.message_service.get_message_by_id", new=AsyncMock(
                return_value=SimpleNamespace(sender="assistant", conversationId=ObjectId(), text="private answer")
            )), patch("app.controllers.message_controller.conversation_service.get_conversation_by_id", new=AsyncMock(
                return_value=SimpleNamespace(userId=owner)
            )):
                response = asyncio.run(self.get(f"/messages/{ObjectId()}/export/pdf"))
            self.assertEqual(response.status_code, 404)
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_owner_can_download_saved_answer_in_both_formats(self):
        user_id, message_id = ObjectId(), ObjectId()
        async def current_user():
            return SimpleNamespace(_id=user_id)
        app.dependency_overrides[get_current_user] = current_user
        try:
            with patch("app.controllers.message_controller.message_service.get_message_by_id", new=AsyncMock(
                return_value=SimpleNamespace(sender="assistant", conversationId=ObjectId(), text="Cited answer [1].")
            )), patch("app.controllers.message_controller.conversation_service.get_conversation_by_id", new=AsyncMock(
                return_value=SimpleNamespace(userId=user_id)
            )), patch("app.controllers.message_controller.message_service.get_question_for_answer", new=AsyncMock(
                return_value="What is the cited rule?"
            )), patch("app.controllers.message_controller.source_service.list_sources_by_message", new=AsyncMock(
                return_value=[SimpleNamespace(filename="law.pdf", metadata={"citation_id": "1", "title": "Law"})]
            )):
                pdf = asyncio.run(self.get(f"/messages/{message_id}/export/pdf"))
                docx = asyncio.run(self.get(f"/messages/{message_id}/export/docx"))
            self.assertEqual(pdf.status_code, 200)
            self.assertTrue(pdf.content.startswith(b"%PDF-"))
            self.assertIn("What is the cited rule?", fitz.open(stream=pdf.content, filetype="pdf")[0].get_text())
            self.assertEqual(docx.status_code, 200)
            with ZipFile(BytesIO(docx.content)) as archive:
                self.assertIn("word/document.xml", archive.namelist())
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_cited_pdf_requires_a_saved_source_and_indexed_file(self):
        user_id, doc_id, source_id, message_id = ObjectId(), str(ObjectId()), ObjectId(), ObjectId()
        source = SimpleNamespace(_id=source_id, metadata={"document_id": doc_id})
        async def current_user():
            return SimpleNamespace(_id=user_id)
        app.dependency_overrides[get_current_user] = current_user
        with TemporaryDirectory() as folder:
            Path(folder, f"{doc_id}.pdf").write_bytes(b"%PDF-1.4\nindexed source")
            database = SimpleNamespace(admin_documents=SimpleNamespace(find_one=AsyncMock(
                return_value={"_id": doc_id, "filename": "official-law.pdf", "status": "indexed", "origin": "upload"}
            )))
            try:
                with patch("app.controllers.message_controller.message_service.get_message_by_id", new=AsyncMock(
                    return_value=SimpleNamespace(sender="assistant", conversationId=ObjectId(), text="answer")
                )), patch("app.controllers.message_controller.conversation_service.get_conversation_by_id", new=AsyncMock(
                    return_value=SimpleNamespace(userId=user_id)
                )), patch("app.controllers.message_controller.source_service.list_sources_by_message", new=AsyncMock(
                    return_value=[source]
                )), patch("app.controllers.message_controller.get_db", return_value=database), patch(
                    "app.controllers.message_controller.ADMIN_UPLOAD_DIR", Path(folder)
                ):
                    response = asyncio.run(self.get(f"/messages/{message_id}/sources/{source_id}/pdf?download=true"))
                    missing = asyncio.run(self.get(f"/messages/{message_id}/sources/{ObjectId()}/pdf"))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, b"%PDF-1.4\nindexed source")
                self.assertIn("attachment", response.headers["content-disposition"])
                self.assertEqual(missing.status_code, 404)
            finally:
                app.dependency_overrides.pop(get_current_user, None)


if __name__ == "__main__":
    unittest.main()
