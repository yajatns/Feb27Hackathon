"""POST /api/analyze-document — file upload → Reka Vision → structured extraction → Neo4j logging."""

import json
import uuid

from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel

from integrations.reka_vision import reka_vision
from integrations.neo4j_client import neo4j_client

router = APIRouter()


class DocumentAnalysisResponse(BaseModel):
    request_id: str
    filename: str
    document_type: str
    extraction: dict | str
    logged_to_graph: bool = False


@router.post("/analyze-document", response_model=DocumentAnalysisResponse)
async def analyze_document(
    file: UploadFile = File(...),
    document_type: str = Form("general"),
    question: str = Form(None),
):
    """Upload a document for Reka Vision analysis.

    Accepts image/PDF uploads, extracts structured data, logs to Neo4j.

    - **file**: The document to analyze (image or PDF)
    - **document_type**: One of: offer_letter, id_document, tax_form,
                         compliance_certificate, general
    - **question**: Optional custom question to ask about the document
    """
    request_id = str(uuid.uuid4())
    file_content = await file.read()

    # Analyze with Reka Vision
    result = await reka_vision.analyze_document(
        file_content=file_content,
        filename=file.filename or "upload",
        document_type=document_type,
        custom_question=question,
    )

    # Log to Neo4j
    logged = False
    try:
        await neo4j_client.log_completion(
            agent_name="RekaVision",
            task=f"analyze_{document_type}",
            result=json.dumps(result.get("extraction", {}), default=str)[:500],
            tool_used="reka_vision",
            hire_request_id=request_id,
        )
        logged = True
    except Exception:
        pass

    return DocumentAnalysisResponse(
        request_id=request_id,
        filename=file.filename or "upload",
        document_type=document_type,
        extraction=result.get("extraction", {}),
        logged_to_graph=logged,
    )
