import asyncio
from datetime import datetime
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from fastapi import HTTPException
from langchain_core.documents import Document

from app.main import app
from app.core.security import get_current_admin, get_current_user
from app.services import rag_service
from app.services.retrieval_service import ConversationalRAGSystem
from app.services.hybrid_retrieval import retrieve_documents
from app.services.auth_service import authenticate_user
from app.schemas.auth import LoginRequest
from app.utils.jwt import create_access_token, decode_access_token


class ClaudeConfigurationTests(unittest.TestCase):
    def test_claude_key_is_required_even_when_google_key_exists(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "", "GOOGLE_API_KEY": "old-key"}):
            self.assertFalse(rag_service.get_rag_status()["configured"])
            self.assertIn("ANTHROPIC_API_KEY", rag_service.get_rag_status()["missing"][0])

    def test_rag_initializes_claude_without_changing_retrieval(self):
        with patch("app.services.retrieval_service.HuggingFaceEmbeddings"), patch(
            "app.services.retrieval_service.Chroma"
        ), patch("app.services.retrieval_service.ChatAnthropic") as chat, patch.object(
            ConversationalRAGSystem, "_setup_retrieval_chain"
        ), patch.dict("os.environ", {"CLAUDE_MODEL": "claude-sonnet-4-6"}):
            ConversationalRAGSystem(anthropic_api_key="test-key")
        self.assertEqual(chat.call_args.kwargs["model"], "claude-sonnet-4-6")
        self.assertEqual(chat.call_args.kwargs["api_key"], "test-key")


class AdminLoginIsolationTests(unittest.TestCase):
    def test_member_cannot_get_admin_token(self):
        member = SimpleNamespace(_id="member", username="member", hashed_password="hash", is_admin=False)
        with patch("app.services.auth_service.get_user_by_login", new=AsyncMock(return_value=member)), patch(
            "app.services.auth_service.verify_password", return_value=True
        ):
            with self.assertRaises(HTTPException) as raised:
                asyncio.run(authenticate_user(LoginRequest(username="member", password="password"), require_admin=True))
        self.assertEqual(raised.exception.status_code, 403)

    def test_admin_login_issues_admin_scoped_token(self):
        admin = SimpleNamespace(_id="admin", username="admin", hashed_password="hash", is_admin=True)
        with patch("app.services.auth_service.get_user_by_login", new=AsyncMock(return_value=admin)), patch(
            "app.services.auth_service.verify_password", return_value=True
        ):
            token = asyncio.run(authenticate_user(LoginRequest(username="admin", password="password"), require_admin=True))
        self.assertEqual(decode_access_token(token)["scope"], "admin")

    def test_app_token_cannot_open_admin_routes(self):
        admin = SimpleNamespace(is_admin=True)
        app_token = create_access_token({"sub": "admin"})
        with self.assertRaises(HTTPException) as raised:
            asyncio.run(get_current_admin(token=app_token, user=admin))
        self.assertEqual(raised.exception.status_code, 403)
        admin_token = create_access_token({"sub": "admin", "scope": "admin"})
        self.assertIs(asyncio.run(get_current_admin(token=admin_token, user=admin)), admin)


class ConversationIsolationTests(unittest.TestCase):
    def test_empty_collection_allows_first_upload_and_returns_no_answer(self):
        collection = SimpleNamespace(count=lambda: 0)
        fake = SimpleNamespace(vector_store=SimpleNamespace(_collection=collection), ask=lambda *_: self.fail("Empty index should not call Claude"))
        previous = rag_service._rag_system
        try:
            rag_service._rag_system = None
            with patch.object(rag_service, "ensure_rag_configured"), patch(
                "app.services.retrieval_service.ConversationalRAGSystem", return_value=fake
            ):
                self.assertIs(rag_service.get_rag_system(), fake)
                response = rag_service.ask_sync("What is GST?")
            self.assertEqual(response["source_documents"], [])
            self.assertIn("could not find", response["answer"])
        finally:
            rag_service._rag_system = previous

    def test_bns_bnss_topic_label_requests_a_detailed_overview(self):
        rag = ConversationalRAGSystem.__new__(ConversationalRAGSystem)
        seen = []
        def invoke(payload):
            seen.append(payload["input"])
            return {"answer": "I could not find the answer in the indexed documents.", "context": []}
        rag.rag_chain = SimpleNamespace(invoke=invoke)
        result = rag.ask("Criminal Law (BNS & BNSS Test)")
        self.assertEqual(result["question"], "Criminal Law (BNS & BNSS Test)")
        self.assertEqual(seen, ["Give a detailed, source-cited overview of BNS and BNSS based on the indexed documents."])

    def test_greeting_needs_no_document_citation(self):
        rag = ConversationalRAGSystem.__new__(ConversationalRAGSystem)
        rag.rag_chain = SimpleNamespace(invoke=lambda _: self.fail("Greeting should not call retrieval"))
        response = rag.ask("hi", [])
        self.assertIn("Hello", response["answer"])
        self.assertEqual(response["source_documents"], [])

    def test_unqualified_income_tax_slabs_question_requests_year_and_taxpayer(self):
        rag = ConversationalRAGSystem.__new__(ConversationalRAGSystem)
        rag.rag_chain = SimpleNamespace(invoke=lambda _: self.fail("Ambiguous rates should not reach the model"))
        for question in ("Income Tax Slabs & Rates?", "ncome Tax Slabs & Rates?"):
            response = rag.ask(question)
            self.assertIn("financial year", response["answer"])
            self.assertIn("individual", response["answer"])
            self.assertIn("old regime", response["answer"])
            self.assertEqual(response["source_documents"], [])

    def test_requests_use_only_their_supplied_history(self):
        rag = ConversationalRAGSystem.__new__(ConversationalRAGSystem)
        seen = []
        def invoke(payload):
            seen.append([m.content for m in payload["chat_history"]])
            return {"answer": "answer", "context": []}
        rag.rag_chain = SimpleNamespace(invoke=invoke)
        first_history = [("user", "private question"), ("assistant", "private reply")]
        rag.ask("follow up", first_history)
        rag.ask("new user's question", [])
        self.assertEqual(seen, [["private question", "private reply"], []])
        self.assertEqual(len(first_history), 2)

    def test_standalone_question_skips_history_rewrite(self):
        rag = ConversationalRAGSystem.__new__(ConversationalRAGSystem)
        seen = []
        rag.rag_chain = SimpleNamespace(invoke=lambda payload: seen.append(payload) or {
            "answer": "I could not find the answer in the indexed documents.", "context": [],
        })
        rag.ask("What is GST under the CGST Act?", [("user", "What is ITR?"), ("assistant", "Income Tax Return")])
        self.assertEqual(seen[0]["chat_history"], [])

    def test_follow_up_keeps_only_recent_context(self):
        rag = ConversationalRAGSystem.__new__(ConversationalRAGSystem)
        seen = []
        rag.rag_chain = SimpleNamespace(invoke=lambda payload: seen.append(payload) or {
            "answer": "I could not find the answer in the indexed documents.", "context": [],
        })
        history = [("user", f"question {n}") if n % 2 == 0 else ("assistant", f"answer {n}") for n in range(10)]
        rag.ask("How does it apply?", history)
        self.assertEqual([message.content for message in seen[0]["chat_history"]],
                         [text for _, text in history[-6:]])

    def test_tax_year_reply_uses_question_it_is_clarifying(self):
        rag = ConversationalRAGSystem.__new__(ConversationalRAGSystem)
        seen = []
        rag.rag_chain = SimpleNamespace(invoke=lambda payload: seen.append(payload) or {
            "answer": "I could not find the answer in the indexed documents.", "context": [],
        })
        history = [("user", "Income Tax Slabs & Rates?"), ("assistant", "Which tax year?")]
        rag.ask("AY 2026-27, individual, new regime", history)
        self.assertEqual([message.content for message in seen[0]["chat_history"]],
                         [text for _, text in history])

    def test_async_wrapper_passes_conversation_history(self):
        received = []
        fake = SimpleNamespace(
            vector_store=SimpleNamespace(_collection=SimpleNamespace(count=lambda: 1)),
            ask=lambda question, history: received.append((question, history)) or {"answer": "ok"},
        )
        history = [("user", "earlier question")]
        try:
            with patch.object(rag_service, "get_rag_system", return_value=fake), patch(
                "app.services.legal_change_service.find_change", new=AsyncMock(return_value=None)
            ):
                response = asyncio.run(rag_service.ask_async("follow up", history))
            self.assertEqual(response["answer"], "ok")
            self.assertEqual(received, [("follow up", history)])
        finally:
            rag_service.shutdown_executor()

    def test_answer_without_support_does_not_cite_retrieved_documents(self):
        rag = ConversationalRAGSystem.__new__(ConversationalRAGSystem)
        unrelated = Document(page_content="GST registration form", metadata={"filename": "gst.pdf"})
        rag.rag_chain = SimpleNamespace(invoke=lambda _: {
            "answer": "I could not find the definition of ITR in the indexed documents.",
            "context": [unrelated],
        })
        self.assertEqual(rag.ask("what is ITR?")["source_documents"], [])

    def test_only_explicitly_cited_passage_is_shown(self):
        rag = ConversationalRAGSystem.__new__(ConversationalRAGSystem)
        relevant = Document(page_content="ITR stands for Income Tax Return.", metadata={"citation_id": "1"})
        unrelated = Document(page_content="GST registration form", metadata={"citation_id": "2"})
        rag.rag_chain = SimpleNamespace(invoke=lambda _: {
            "answer": "ITR stands for Income Tax Return [1].", "context": [relevant, unrelated],
        })
        result = rag.ask("what is ITR?")
        self.assertEqual(result["source_documents"], [relevant])
        self.assertEqual(result["answer"], "ITR stands for Income Tax Return [1].")

    def test_partially_sourced_answer_keeps_its_source_with_a_verification_gap(self):
        rag = ConversationalRAGSystem.__new__(ConversationalRAGSystem)
        historical = Document(page_content="Historical tax rate provision", metadata={"citation_id": "1", "filename": "old.pdf"})
        rag.rag_chain = SimpleNamespace(invoke=lambda _: {
            "answer": "The older rate was set out in the Act [1]. I could not find a later amendment in the indexed documents.",
            "context": [historical],
        })
        result = rag.ask("What rate applied and has it changed?")
        self.assertEqual(result["source_documents"], [historical])

    def test_answer_with_unknown_source_number_is_rejected(self):
        rag = ConversationalRAGSystem.__new__(ConversationalRAGSystem)
        relevant = Document(page_content="A supported provision", metadata={"citation_id": "1"})
        rag.rag_chain = SimpleNamespace(invoke=lambda _: {
            "answer": "Supported [1]. Unverified extra claim [2].",
            "context": [relevant],
        })
        result = rag.ask("Explain the provision")
        self.assertEqual(result["answer"], "I could not find the answer in the indexed documents.")
        self.assertEqual(result["source_documents"], [])

    def test_comma_separated_citations_keep_both_passages(self):
        rag = ConversationalRAGSystem.__new__(ConversationalRAGSystem)
        first = Document(page_content="Late fee for delayed return", metadata={"citation_id": "1"})
        second = Document(page_content="Penalty for a contravention", metadata={"citation_id": "5"})
        rag.rag_chain = SimpleNamespace(invoke=lambda _: {
            "answer": "The older Act describes a late fee and a penalty [1, 5].",
            "context": [first, second],
        })
        self.assertEqual(rag.ask("late filing penalties")["source_documents"], [first, second])

    def test_historical_late_fee_answer_is_dated_and_scoped(self):
        rag = ConversationalRAGSystem.__new__(ConversationalRAGSystem)
        source = Document(page_content="Section 47 provides a late fee.", metadata={
            "citation_id": "1", "filename": "Central_Goods_and_Services_Tax_Act_2017.pdf",
        })
        rag.rag_chain = SimpleNamespace(invoke=lambda _: {
            "answer": "Section 47 provides a late fee [1].", "context": [source],
        })
        answer = rag.ask("GST Late Filing and Penalties")["answer"]
        self.assertIn("2017 document text", answer)
        self.assertIn("current amounts and applicability have not been verified", answer)
        self.assertIn("does not establish every possible penalty", answer)

    def test_uncited_answer_is_withheld(self):
        rag = ConversationalRAGSystem.__new__(ConversationalRAGSystem)
        rag.rag_chain = SimpleNamespace(invoke=lambda _: {
            "answer": "Unverified claim.", "context": [],
        })
        result = rag.ask("question")
        self.assertEqual(result["answer"], "I could not find the answer in the indexed documents.")
        self.assertEqual(result["source_documents"], [])


class HybridRetrievalTests(unittest.TestCase):
    def test_numbered_notification_prefers_exact_rate_category(self):
        snapshot = {"documents": [
            "Notification No. 30/2017-Central Tax (Rate) changes the rate of a service.",
            "Notification No. 30/2017-Central Tax extends return filing dates.",
        ], "metadatas": [
            {"filename": "rate.pdf", "title": "CGST Rate Notification 30/2017-Central Tax (Rate) — 29 Sep 2017", "page": 1},
            {"filename": "tax.pdf", "title": "CGST Notification 30/2017-Central Tax — 11 Sep 2017", "page": 1},
        ]}
        store = SimpleNamespace(
            _collection=SimpleNamespace(get=lambda **_: snapshot),
            similarity_search_with_relevance_scores=lambda *_, **__: [],
        )
        self.assertEqual(retrieve_documents(store, "What did Notification 30/2017-Central Tax do?")[0].metadata["filename"], "tax.pdf")
        self.assertEqual(retrieve_documents(store, "What did Rate Notification 30/2017-Central Tax (Rate) do?")[0].metadata["filename"], "rate.pdf")

    def test_named_finance_act_section_surfaces_amendment_in_punjabi_question(self):
        unrelated = "Section 16(4) concerns tax invoices and debit notes."
        amendment = '120. In section 16 of the Central Goods and Services Tax Act, in sub-section (4), the words “invoice relating to such” shall be omitted.'
        other_year = "120. A different amendment in Finance Act 2021."
        snapshot = {"documents": [unrelated, amendment, other_year], "metadatas": [
            {"filename": "cgst.pdf", "page": 18},
            {"filename": "finance_act_2020.pdf", "page": 56},
            {"filename": "finance_act_2021.pdf", "page": 50},
        ]}
        store = SimpleNamespace(
            _collection=SimpleNamespace(get=lambda **_: snapshot),
            similarity_search_with_relevance_scores=lambda *_, **__: [],
        )
        result = retrieve_documents(store, "Finance Act 2020 de Section 120 ne CGST Section 16(4) vich ki change kita? Ki debit note de ITC di time limit original invoice di date naal linked rehndi hai?")
        self.assertEqual(result[0].metadata["filename"], "finance_act_2020.pdf")
        self.assertEqual(result[0].metadata["page"], 56)

    def test_bns_bnss_topic_uses_both_acts_opening_pages(self):
        snapshot = {"documents": [
            "Criminal law can apply to companies.",
            "THE BHARATIYA NYAYA SANHITA, 2023. An Act relating to offences.",
            "THE BHARATIYA NAGARIK SURAKSHA SANHITA, 2023. An Act relating to criminal procedure.",
        ], "metadatas": [
            {"filename": "companies.pdf", "title": "The Companies Act, 2013", "page": 87},
            {"filename": "bns.pdf", "title": "The Bharatiya Nyaya Sanhita, 2023", "page": 1},
            {"filename": "bnss.pdf", "title": "The Bharatiya Nagarik Suraksha Sanhita, 2023", "page": 1},
        ]}
        store = SimpleNamespace(
            _collection=SimpleNamespace(get=lambda **_: snapshot),
            similarity_search_with_relevance_scores=lambda *_, **__: [],
        )
        result = retrieve_documents(store, "Criminal Law (BNS & BNSS Test)")
        self.assertEqual({doc.metadata["filename"] for doc in result[:2]}, {"bns.pdf", "bnss.pdf"})

    def test_contract_definition_under_named_act_beats_incidental_contract_use(self):
        incidental = "A contingent contract is a contract to do something later. Contract contract contract."
        definition = "(h) An agreement enforceable by law is a contract."
        snapshot = {"documents": [incidental, definition], "metadatas": [
            {"filename": "contract.pdf", "title": "The Indian Contract Act, 1872", "page": 20},
            {"filename": "contract.pdf", "title": "The Indian Contract Act, 1872", "page": 11},
        ]}
        store = SimpleNamespace(
            _collection=SimpleNamespace(get=lambda **_: snapshot),
            similarity_search_with_relevance_scores=lambda *_, **__: [],
        )
        result = retrieve_documents(store, "What is a contract under the Indian Contract Act, 1872?")
        self.assertEqual(result[0].metadata["page"], 11)

    def test_company_definition_under_named_act_beats_unrelated_act(self):
        unrelated = '“company” means a corporation for this procedure.'
        definition = '“company” means a company incorporated under this Act or under any previous company law.'
        snapshot = {"documents": [unrelated, definition], "metadatas": [
            {"filename": "bnss.pdf", "title": "The Bharatiya Nagarik Suraksha Sanhita, 2023", "page": 20},
            {"filename": "companies.pdf", "title": "The Companies Act, 2013", "page": 3},
        ]}
        store = SimpleNamespace(
            _collection=SimpleNamespace(get=lambda **_: snapshot),
            similarity_search_with_relevance_scores=lambda *_, **__: [],
        )
        result = retrieve_documents(store, "What is a company under the Companies Act, 2013?")
        self.assertEqual(result[0].metadata["filename"], "companies.pdf")

    def test_late_filing_topic_finds_late_fee_for_returns(self):
        forms = "GST filing penalty GST filing penalty"
        act = "A person who fails to furnish returns by the due date shall pay a late fee."
        snapshot = {"documents": [forms, act], "metadatas": [
            {"filename": "forms.pdf", "page": 5},
            {"filename": "Central_Goods_and_Services_Tax_Act_2017.pdf", "page": 37},
        ]}
        store = SimpleNamespace(
            _collection=SimpleNamespace(get=lambda **_: snapshot),
            similarity_search_with_relevance_scores=lambda *_, **__: [
                (Document(page_content=forms, metadata=snapshot["metadatas"][0]), 0.6)
            ],
        )
        result = retrieve_documents(store, "GST Late Filing and Penalties")
        self.assertEqual(result[0].metadata["page"], 37)

    def test_gst_definition_beats_forms_that_only_repeat_gst(self):
        forms = "GST form GST return GST payment."
        definition = "GST stands for Goods and Services Tax, levied on supplies in India."
        snapshot = {"documents": [forms, definition], "metadatas": [
            {"filename": "forms.pdf", "page": 5},
            {"filename": "gst-flyer.pdf", "page": 1, "title": "Benefits of Goods and Services Tax (GST)"},
        ]}
        store = SimpleNamespace(
            _collection=SimpleNamespace(get=lambda **_: snapshot),
            similarity_search_with_relevance_scores=lambda *_, **__: [
                (Document(page_content=forms, metadata=snapshot["metadatas"][0]), 0.6)
            ],
        )
        result = retrieve_documents(store, "what is gst?")
        self.assertEqual(result[0].metadata["filename"], "gst-flyer.pdf")

    def test_outside_gst_question_uses_scope_provisions_not_incidental_circulars(self):
        circular = "GST applies outside a special zone, but this circular concerns registration."
        scope = "7. (1) Scope of supply. (2) Activities specified in Schedule III shall be treated neither as a supply of goods nor services."
        levy = "9. (1) Central tax on all intra-State supplies except alcoholic liquor for human consumption. (2) Petroleum crude and diesel are levied from a notified date."
        schedule = "SCHEDULE  III\n[See section 7]\nServices by an employee to the employer."
        constitution = '(12A) “goods and services tax” means any tax on supply except alcoholic liquor for human consumption.'
        amendment = '4. In the principal Act, in Schedule III, paragraph 6 substitutes “specified actionable claims”.'
        commencement = 'The 1st day of October, 2023 is appointed as the date on which the Act comes into force.'
        contents = [circular, scope, levy, schedule, constitution, amendment, commencement]
        metadatas = [
            {"title": "CGST Circular 1/2024", "page": 1},
            {"title": "THE CENTRAL GOODS AND SERVICES TAX ACT, 2017", "page": 13},
            {"title": "THE CENTRAL GOODS AND SERVICES TAX ACT, 2017", "page": 13},
            {"title": "THE CENTRAL GOODS AND SERVICES TAX ACT, 2017", "page": 103},
            {"title": "CONSTITUTION OF INDIA", "page": 255},
            {"title": "THE CENTRAL GOODS AND SERVICES TAX (AMENDMENT) ACT, 2023", "page": 2},
            {"title": "CGST Notification 48/2023-Central Tax — 29 Sep 2023", "page": 1},
        ]
        store = SimpleNamespace(
            _collection=SimpleNamespace(get=lambda **_: {"documents": contents, "metadatas": metadatas}),
            similarity_search_with_relevance_scores=lambda *_, **__: [(Document(page_content=circular, metadata=metadatas[0]), 0.9)],
        )
        result = retrieve_documents(store, "What is kept outside GST?")
        self.assertEqual({doc.metadata["page"] for doc in result}, {1, 2, 13, 103, 255})
        self.assertTrue(all("Circular" not in doc.metadata["title"] for doc in result))

    def test_exact_acronym_definition_outranks_unrelated_semantic_matches(self):
        itr = "ITR — Income Tax Return. ITR stands for Income Tax Return."
        gst = "Goods and Services Tax registration return."
        snapshot = {"documents": [gst, itr], "metadatas": [
            {"filename": "gst.pdf", "page": 1},
            {"filename": "itr.pdf", "page": 1},
        ]}
        store = SimpleNamespace(
            _collection=SimpleNamespace(get=lambda **_: snapshot),
            similarity_search_with_relevance_scores=lambda *_, **__: [
                (Document(page_content=gst, metadata=snapshot["metadatas"][0]), 0.55)
            ],
        )
        result = retrieve_documents(store, "what is itr?")
        self.assertEqual([doc.metadata["filename"] for doc in result], ["itr.pdf"])

    def test_new_document_is_read_from_index_on_each_query(self):
        contents = ["GST return form"]
        store = SimpleNamespace(
            _collection=SimpleNamespace(get=lambda **_: {
                "documents": contents,
                "metadatas": [{"filename": "gst.pdf"}] if len(contents) == 1 else [
                    {"filename": "gst.pdf"}, {"filename": "itr.pdf"}
                ],
            }),
            similarity_search_with_relevance_scores=lambda *_, **__: [],
        )
        self.assertEqual(retrieve_documents(store, "what is itr?"), [])
        contents.append("ITR — Income Tax Return")
        self.assertEqual(retrieve_documents(store, "what is itr?")[0].metadata["filename"], "itr.pdf")


class UserAuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.own_id = "000000000000000000000001"
        self.other_id = "000000000000000000000002"

    def tearDown(self):
        app.dependency_overrides.clear()
        self.client.close()

    def test_user_routes_reject_unauthenticated_requests(self):
        for method in ["get", "put", "delete"]:
            kwargs = {"json": {"username": "updated"}} if method == "put" else {}
            with self.subTest(method=method):
                response = getattr(self.client, method)(f"/users/{self.other_id}", **kwargs)
                self.assertEqual(response.status_code, 401)

    def test_user_cannot_access_another_account(self):
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(_id=self.own_id)
        for method in ["get", "put", "delete"]:
            kwargs = {"json": {"username": "updated"}} if method == "put" else {}
            with self.subTest(method=method):
                response = getattr(self.client, method)(f"/users/{self.other_id}", **kwargs)
                self.assertEqual(response.status_code, 404)

    def test_owner_can_read_their_account(self):
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(_id=self.own_id)
        user = SimpleNamespace(_id=self.own_id, username="localtest", email=None, createdAt=datetime(2026, 1, 1))
        with patch("app.controllers.user_controller.user_service.get_user_by_id", new=AsyncMock(return_value=user)):
            response = self.client.get(f"/users/{self.own_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], self.own_id)


    def test_profile_cannot_take_another_accounts_email(self):
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(_id=self.own_id)
        with patch("app.controllers.user_controller.user_service.get_user_by_login", new=AsyncMock(return_value=SimpleNamespace(_id=self.other_id))), patch(
            "app.controllers.user_controller.user_service.update_user", new=AsyncMock()
        ) as update:
            response = self.client.put(f"/users/{self.own_id}", json={"email": "occupied@example.com"})
        self.assertEqual(response.status_code, 400)
        update.assert_not_awaited()


class SourceAuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(_id="owner")

    def tearDown(self):
        app.dependency_overrides.clear()
        self.client.close()

    def test_another_users_sources_are_not_exposed(self):
        message = SimpleNamespace(conversationId="conversation")
        with patch("app.controllers.message_controller.message_service.get_message_by_id", new=AsyncMock(return_value=message)), patch(
            "app.controllers.message_controller.conversation_service.get_conversation_by_id", new=AsyncMock(return_value=SimpleNamespace(userId="someone-else"))
        ), patch("app.controllers.message_controller.source_service.list_sources_by_message", new=AsyncMock()) as sources:
            response = self.client.get("/messages/message/sources")
        self.assertEqual(response.status_code, 404)
        sources.assert_not_awaited()

    def test_owner_receives_actual_source_text_and_page_metadata(self):
        message = SimpleNamespace(conversationId="conversation")
        source = SimpleNamespace(_id="source", messageId="message", filename="act.pdf", content="Exact retrieved text", metadata={"page": 7}, createdAt=datetime(2026, 1, 1))
        with patch("app.controllers.message_controller.message_service.get_message_by_id", new=AsyncMock(return_value=message)), patch(
            "app.controllers.message_controller.conversation_service.get_conversation_by_id", new=AsyncMock(return_value=SimpleNamespace(userId="owner"))
        ), patch("app.controllers.message_controller.source_service.list_sources_by_message", new=AsyncMock(return_value=[source])):
            response = self.client.get("/messages/message/sources")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["content"], "Exact retrieved text")
        self.assertEqual(response.json()[0]["metadata"]["page"], 7)


if __name__ == "__main__":
    unittest.main()
