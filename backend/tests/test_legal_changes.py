"""Date-scoped legal comparisons must fail closed without reviewed evidence."""

import asyncio
from datetime import date
import unittest
from unittest.mock import AsyncMock, patch

from app.services import legal_change_service, rag_service


def sample_change():
    return {
        "law_keyword": "CGST", "provision": "Section 16(4)",
        "before_text": "The earlier provision used the invoice date for this limit.",
        "after_text": "The amended provision treats a debit note separately.",
        "before_from": "2017-07-01", "effective_from": "2021-01-01",
        "verified_through": "2025-12-31",
        "before_source_url": "https://www.gstcouncil.gov.in/before.pdf",
        "after_source_url": "https://www.gstcouncil.gov.in/after.pdf",
        "commencement_source_url": "https://egazette.gov.in/effective.pdf",
    }


class ReviewedComparisonTests(unittest.TestCase):
    def test_requires_law_and_exact_provision(self):
        record = sample_change()
        self.assertTrue(legal_change_service.matches_question(
            record, "CGST Section 16(4): pehle ki si te hun ki hai?"))
        self.assertFalse(legal_change_service.matches_question(record, "CGST Section 16(2) current rule"))
        self.assertFalse(legal_change_service.matches_question(record, "Section 16(4) current rule"))

    def test_only_official_https_urls_are_accepted(self):
        self.assertTrue(legal_change_service.official_url("https://egazette.gov.in/notice.pdf"))
        self.assertFalse(legal_change_service.official_url("https://fake-gov.in/notice.pdf"))
        self.assertFalse(legal_change_service.official_url("http://egazette.gov.in/notice.pdf"))

    def test_stale_verification_cannot_claim_current_law(self):
        result = legal_change_service.comparison_answer(
            sample_change(), "CGST Section 16(4) before and now?", today=date(2026, 11, 12))
        self.assertIn("Later verified position", result["answer"])
        self.assertIn("changes after that date have not been checked", result["answer"])
        self.assertNotIn("Current verified position", result["answer"])
        self.assertEqual([s.metadata["citation_id"] for s in result["source_documents"]], ["1", "2", "3"])
        self.assertTrue(all(s.metadata["source_url"].startswith("https://") for s in result["source_documents"]))

    def test_current_label_requires_verification_through_today(self):
        record = sample_change()
        record["verified_through"] = "2026-11-12"
        answer = legal_change_service.comparison_answer(
            record, "CGST Section 16(4) current rule?", today=date(2026, 11, 12))["answer"]
        self.assertIn("Current verified position", answer)
        self.assertIn("Verified as of 2026-11-12", answer)

    def test_temporal_question_without_reviewed_record_does_not_call_model(self):
        with patch.object(legal_change_service, "find_change", new=AsyncMock(return_value=None)), patch.object(
            rag_service, "get_executor", side_effect=AssertionError("No model call is allowed")
        ):
            answer = asyncio.run(rag_service.ask_async("What is the current CGST Section 16(4)?"))
        self.assertIn("could not verify", answer["answer"])
        self.assertEqual(answer["source_documents"], [])

    def test_reviewed_record_is_used_without_model_guess(self):
        with patch.object(legal_change_service, "find_change", new=AsyncMock(return_value=sample_change())), patch.object(
            rag_service, "get_executor", side_effect=AssertionError("No model call is allowed")
        ):
            answer = asyncio.run(rag_service.ask_async("CGST Section 16(4) before and now?"))
        self.assertEqual(len(answer["source_documents"]), 3)


if __name__ == "__main__":
    unittest.main()
