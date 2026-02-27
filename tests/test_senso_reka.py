"""Tests for T3: Senso policy ingestion + Reka Vision document analysis."""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# ---------------------------------------------------------------------------
# Senso ingestion script tests
# ---------------------------------------------------------------------------


class TestSensoIngestion:
    """Test the Senso ingestion script and policy files."""

    def test_policy_files_exist(self):
        """All 4 policy markdown files exist and have content."""
        policies_dir = Path(__file__).parent.parent / "scripts" / "policies"
        expected = [
            "hr-policy.md",
            "it-provisioning.md",
            "finance-policy.md",
            "compliance-checklist.md",
        ]
        for filename in expected:
            filepath = policies_dir / filename
            assert filepath.exists(), f"Missing policy file: {filename}"
            content = filepath.read_text()
            assert len(content) > 500, f"Policy file too short: {filename}"

    def test_hr_policy_has_salary_bands(self):
        """HR policy contains salary band data."""
        path = Path(__file__).parent.parent / "scripts" / "policies" / "hr-policy.md"
        content = path.read_text()
        assert "Senior Engineer" in content
        assert "$155K" in content or "155" in content
        assert "L5" in content or "Level 5" in content

    def test_finance_policy_has_expense_limits(self):
        """Finance policy contains expense limits and approvals."""
        path = Path(__file__).parent.parent / "scripts" / "policies" / "finance-policy.md"
        content = path.read_text()
        assert "expense" in content.lower()
        assert "approval" in content.lower()
        assert "$500" in content or "500" in content

    def test_compliance_has_state_requirements(self):
        """Compliance checklist covers required states."""
        path = Path(__file__).parent.parent / "scripts" / "policies" / "compliance-checklist.md"
        content = path.read_text()
        for state in ["California", "New York", "Texas", "Washington"]:
            assert state in content, f"Missing state: {state}"

    def test_it_policy_has_equipment(self):
        """IT policy covers equipment provisioning."""
        path = Path(__file__).parent.parent / "scripts" / "policies" / "it-provisioning.md"
        content = path.read_text()
        assert "laptop" in content.lower()
        assert "MacBook" in content
        assert "access" in content.lower()

    def test_ingestion_script_exists(self):
        """Ingestion script exists and is importable."""
        script = Path(__file__).parent.parent / "scripts" / "ingest_senso.py"
        assert script.exists()

    @pytest.mark.asyncio
    async def test_ingestion_uploads_documents(self):
        """Test ingestion script uploads all 4 documents."""
        # Import the script's functions
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from ingest_senso import ingest_document, POLICY_FILES

        assert len(POLICY_FILES) == 4

        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "doc_123", "status": "created"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        result = await ingest_document(mock_client, "test.md", "# Test", "text/markdown")
        assert result["id"] == "doc_123"
        mock_client.post.assert_called_once()


# ---------------------------------------------------------------------------
# Senso policy search helper tests
# ---------------------------------------------------------------------------


class TestSensoPolicies:
    """Test the Senso policy search helper."""

    def test_detect_policy_category_hr(self):
        from integrations.senso_policies import detect_policy_category
        cats = detect_policy_category("What is the salary band for senior engineer?")
        assert "hr" in cats

    def test_detect_policy_category_finance(self):
        from integrations.senso_policies import detect_policy_category
        cats = detect_policy_category("What is our expense limit for travel?")
        assert "finance" in cats

    def test_detect_policy_category_it(self):
        from integrations.senso_policies import detect_policy_category
        cats = detect_policy_category("What laptop does a new engineer get?")
        assert "it" in cats

    def test_detect_policy_category_compliance(self):
        from integrations.senso_policies import detect_policy_category
        cats = detect_policy_category("What are California compliance requirements?")
        assert "compliance" in cats

    def test_detect_policy_category_default(self):
        from integrations.senso_policies import detect_policy_category
        cats = detect_policy_category("tell me about something random")
        assert len(cats) > 0  # Should return defaults

    @pytest.mark.asyncio
    async def test_is_policy_question(self):
        from integrations.senso_policies import is_policy_question
        assert await is_policy_question("What is our salary policy?")
        assert await is_policy_question("What's the expense limit?")
        assert await is_policy_question("Do we provide laptops?")
        assert not await is_policy_question("What's the weather today?")

    @pytest.mark.asyncio
    async def test_search_policies_handles_error(self):
        """Policy search returns graceful error when Senso is unavailable."""
        from integrations.senso_policies import search_policies
        with patch("integrations.senso_policies.senso_client") as mock:
            mock.search_policy = AsyncMock(side_effect=Exception("API down"))
            result = await search_policies("salary band")
            assert "error" in result
            assert result["categories"]


# ---------------------------------------------------------------------------
# Reka Vision client tests
# ---------------------------------------------------------------------------


class TestRekaVision:
    """Test the Reka Vision document processor."""

    def test_detect_media_type(self):
        from integrations.reka_vision import reka_vision
        assert reka_vision._detect_media_type("doc.pdf") == "application/pdf"
        assert reka_vision._detect_media_type("photo.png") == "image/png"
        assert reka_vision._detect_media_type("scan.jpg") == "image/jpeg"
        assert reka_vision._detect_media_type("unknown") == "application/octet-stream"

    def test_parse_structured_json(self):
        from integrations.reka_vision import reka_vision
        result = reka_vision._parse_structured('{"name": "test", "value": 42}')
        assert isinstance(result, dict)
        assert result["name"] == "test"

    def test_parse_structured_json_block(self):
        from integrations.reka_vision import reka_vision
        result = reka_vision._parse_structured('Here is the data:\n```json\n{"name": "test"}\n```\nDone.')
        assert isinstance(result, dict)
        assert result["name"] == "test"

    def test_parse_structured_plain_text(self):
        from integrations.reka_vision import reka_vision
        result = reka_vision._parse_structured("This is plain text analysis")
        assert isinstance(result, str)

    def test_extraction_prompts_exist(self):
        from integrations.reka_vision import RekaVisionProcessor
        expected_types = ["offer_letter", "id_document", "tax_form", "compliance_certificate", "general"]
        for dt in expected_types:
            assert dt in RekaVisionProcessor.EXTRACTION_PROMPTS

    @pytest.mark.asyncio
    async def test_analyze_document_mock(self):
        """Test document analysis with mocked Reka API."""
        from integrations.reka_vision import reka_vision

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"document_type": "offer_letter", "name": "John"}'}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(reka_vision.client, "post", new_callable=AsyncMock, return_value=mock_response):
            result = await reka_vision.analyze_document(
                file_content=b"fake pdf content",
                filename="offer.pdf",
                document_type="offer_letter",
            )
            assert result["document_type"] == "offer_letter"
            assert isinstance(result["extraction"], dict)
            assert result["extraction"]["name"] == "John"


# ---------------------------------------------------------------------------
# Document analysis route tests
# ---------------------------------------------------------------------------


class TestDocumentAnalysisRoute:
    """Test the /api/analyze-document endpoint."""

    def test_route_exists(self):
        """Document analysis route is registered."""
        from routes.documents import router
        routes = [r.path for r in router.routes]
        assert "/analyze-document" in routes

    @pytest.mark.asyncio
    async def test_analyze_document_endpoint(self):
        """Test the endpoint with mocked Reka Vision."""
        from fastapi.testclient import TestClient
        from unittest.mock import patch

        # Create a minimal app for testing
        from fastapi import FastAPI
        from routes.documents import router

        test_app = FastAPI()
        test_app.include_router(router, prefix="/api")

        mock_result = {
            "filename": "test.pdf",
            "document_type": "general",
            "extraction": {"document_type": "invoice", "amount": "$500"},
            "raw_response": {},
        }

        with patch("routes.documents.reka_vision") as mock_reka, \
             patch("routes.documents.neo4j_client") as mock_neo4j:
            mock_reka.analyze_document = AsyncMock(return_value=mock_result)
            mock_neo4j.log_completion = AsyncMock(return_value={})

            client = TestClient(test_app)
            response = client.post(
                "/api/analyze-document",
                files={"file": ("test.pdf", b"fake content", "application/pdf")},
                data={"document_type": "general"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["filename"] == "test.pdf"
            assert data["document_type"] == "general"
            assert "extraction" in data


# ---------------------------------------------------------------------------
# Query route policy enhancement tests
# ---------------------------------------------------------------------------


class TestQueryPolicyRouting:
    """Test that query route pre-fetches Senso for policy questions."""

    def test_query_imports_policy_helper(self):
        """Query route imports the policy search helper."""
        import routes.query as q
        assert hasattr(q, "search_policies")
        assert hasattr(q, "is_policy_question")
