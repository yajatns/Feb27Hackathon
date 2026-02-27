"""Reka Vision document processor — structured extraction from uploaded documents."""

import base64
import json
from typing import BinaryIO

import httpx
from app.config import settings


class RekaVisionProcessor:
    """Analyze documents (images, PDFs) using Reka Vision API."""

    # Document type detection and extraction prompts
    EXTRACTION_PROMPTS = {
        "offer_letter": (
            "Extract the following from this offer letter: "
            "candidate_name, role/title, department, salary/compensation, "
            "start_date, location, signing_bonus, equity_grant, benefits_summary. "
            "Return as structured JSON."
        ),
        "id_document": (
            "Extract the following from this identity document: "
            "document_type (passport/drivers_license/state_id), "
            "full_name, date_of_birth, document_number, expiration_date, "
            "issuing_authority. Return as structured JSON."
        ),
        "tax_form": (
            "Extract the following from this tax form: "
            "form_type (W-4/W-9/1099/W-2), tax_year, "
            "name, ssn_last_four, filing_status, address, "
            "employer_name, total_wages, tax_withheld. Return as structured JSON."
        ),
        "compliance_certificate": (
            "Extract the following from this compliance certificate: "
            "certificate_type, issued_to, issued_by, issue_date, "
            "expiration_date, certification_number, scope, status. "
            "Return as structured JSON."
        ),
        "general": (
            "Analyze this document and extract all key information. "
            "Identify the document type, then extract relevant fields. "
            "Return as structured JSON with document_type and extracted_data fields."
        ),
    }

    def __init__(self):
        self.base_url = settings.reka_base_url
        self.api_key = settings.reka_api_key
        self.client = httpx.AsyncClient(timeout=120.0)

    @property
    def headers(self) -> dict:
        return {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

    async def analyze_document(
        self,
        file_content: bytes,
        filename: str,
        document_type: str = "general",
        custom_question: str | None = None,
    ) -> dict:
        """Analyze an uploaded document using Reka Vision.

        Args:
            file_content: Raw bytes of the uploaded file.
            filename: Original filename (used to detect content type).
            document_type: One of offer_letter, id_document, tax_form,
                           compliance_certificate, general.
            custom_question: Override the default extraction prompt.

        Returns:
            {
                "filename": str,
                "document_type": str,
                "extraction": dict | str,
                "raw_response": dict,
            }
        """
        question = custom_question or self.EXTRACTION_PROMPTS.get(
            document_type, self.EXTRACTION_PROMPTS["general"]
        )

        # Encode file as base64 for the API
        file_b64 = base64.b64encode(file_content).decode("utf-8")
        media_type = self._detect_media_type(filename)

        # Use Reka chat multimodal endpoint with image input
        payload = {
            "model": "reka-flash",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": f"data:{media_type};base64,{file_b64}",
                        },
                        {
                            "type": "text",
                            "text": question,
                        },
                    ],
                }
            ],
            "max_tokens": 2048,
        }

        try:
            resp = await self.client.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self.headers,
                json=payload,
            )
            resp.raise_for_status()
            result = resp.json()
        except httpx.HTTPStatusError as e:
            return {
                "filename": filename,
                "document_type": document_type,
                "extraction": {"error": f"Reka API error: {e.response.status_code}"},
                "raw_response": {"error": e.response.text[:500]},
            }
        except Exception as e:
            return {
                "filename": filename,
                "document_type": document_type,
                "extraction": {"error": str(e)},
                "raw_response": {},
            }

        # Parse the response
        content = self._extract_content(result)
        extraction = self._parse_structured(content)

        return {
            "filename": filename,
            "document_type": document_type,
            "extraction": extraction,
            "raw_response": result,
        }

    async def analyze_document_url(
        self,
        url: str,
        document_type: str = "general",
        custom_question: str | None = None,
    ) -> dict:
        """Analyze a document from a URL."""
        question = custom_question or self.EXTRACTION_PROMPTS.get(
            document_type, self.EXTRACTION_PROMPTS["general"]
        )

        payload = {
            "model": "reka-flash",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": url},
                        {"type": "text", "text": question},
                    ],
                }
            ],
            "max_tokens": 2048,
        }

        try:
            resp = await self.client.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self.headers,
                json=payload,
            )
            resp.raise_for_status()
            result = resp.json()
        except httpx.HTTPStatusError as e:
            return {
                "filename": url,
                "document_type": document_type,
                "extraction": {"error": f"Reka API error: {e.response.status_code}"},
                "raw_response": {"error": e.response.text[:500]},
            }
        except Exception as e:
            return {
                "filename": url,
                "document_type": document_type,
                "extraction": {"error": str(e)},
                "raw_response": {},
            }

        content = self._extract_content(result)
        extraction = self._parse_structured(content)

        return {
            "filename": url,
            "document_type": document_type,
            "extraction": extraction,
            "raw_response": result,
        }

    def _detect_media_type(self, filename: str) -> str:
        """Detect MIME type from filename."""
        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
        return {
            "pdf": "application/pdf",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "gif": "image/gif",
            "webp": "image/webp",
            "tiff": "image/tiff",
            "tif": "image/tiff",
            "bmp": "image/bmp",
        }.get(ext, "application/octet-stream")

    def _extract_content(self, result: dict) -> str:
        """Extract text content from Reka API response."""
        choices = result.get("choices", result.get("data", []))
        if choices and isinstance(choices, list):
            msg = choices[0].get("message", choices[0])
            return msg.get("content", str(msg))
        return result.get("text", result.get("content", str(result)))

    def _parse_structured(self, content: str) -> dict | str:
        """Try to parse structured JSON from model output."""
        # Try to find JSON block in the response
        if "```json" in content:
            start = content.index("```json") + 7
            end = content.index("```", start)
            content = content[start:end].strip()
        elif "```" in content:
            start = content.index("```") + 3
            end = content.index("```", start)
            content = content[start:end].strip()

        try:
            return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return content

    async def close(self):
        await self.client.aclose()


reka_vision = RekaVisionProcessor()
