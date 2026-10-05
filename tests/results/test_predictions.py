from dataclasses import replace

import pytest

from indico_toolkit.results import (
    NULL_CITATION,
    NULL_SPAN,
    DocumentExtraction,
    Extraction,
    FormExtraction,
    FormExtractionType,
    Group,
    Prediction,
    Summarization,
    Unbundling,
)


@pytest.fixture
def document_extraction() -> DocumentExtraction:
    return DocumentExtraction.from_dict(
        None,  # type: ignore[ty:invalid-argument-type]
        None,  # type: ignore[ty:invalid-argument-type]
        None,
        {
            "label": "Agency",
            "confidence": {"Agency": 0.99},
            "text": "ORIGINAL_OCR",
            "spans": [{"page_num": 0, "start": 35, "end": 61}],
            "groupings": [],
            "normalized": {
                "text": "ORIGINAL_GENAI",
                "formatted": "NORMALIZED",
                "structured": None,
            },
        },
    )


@pytest.fixture
def form_extraction() -> FormExtraction:
    return FormExtraction.from_dict(
        None,  # type: ignore[ty:invalid-argument-type]
        None,  # type: ignore[ty:invalid-argument-type]
        None,
        {
            "type": "text",
            "label": "Agency",
            "confidence": {"Agency": 1.0},
            "text": "ORIGINAL_OCR",
            "page_num": 0,
            "top": 201,
            "left": 73,
            "right": 1266,
            "bottom": 448,
            "normalized": {
                "text": "ORIGINAL_GENAI",
                "formatted": "NORMALIZED",
                "structured": None,
            },
        },
    )


@pytest.fixture
def summarization() -> Summarization:
    return Summarization.from_dict(
        None,  # type: ignore[ty:invalid-argument-type]
        None,  # type: ignore[ty:invalid-argument-type]
        None,
        {
            "label": "Accounting Summary",
            "confidence": {"Accounting Summary": 1.0},
            "text": """Vendor: HubSpot, Inc.
Date: 06/21/2016
Number: 579266
Total: $1,301.56
Billing Address:
186 SOUTH STREET
SUITE 400
Boston MA 02111
US
Line Items:
- HubSpot Enterprise (1): $1,200.00
- Included Contacts (10): $0.00
- Enterprise Contacts - Per 1000 (5): $25.00 [1]""",
            "citations": [
                {
                    "document": {"page_num": 0, "start": 0, "end": 758},
                    "response": {"start": 285, "end": 288},
                }
            ],
        },
    )


@pytest.fixture
def unbundling() -> Unbundling:
    return Unbundling.from_dict(
        None,  # type: ignore[ty:invalid-argument-type]
        None,  # type: ignore[ty:invalid-argument-type]
        None,
        {
            "label": "Invoice",
            "confidence": {
                "Invoice": 0.975,
                "Purchase Order": 0.0245,
            },
            "spans": [{"page_num": 0, "start": 0, "end": 762}],
        },
    )


def test_next_group() -> None:
    group = Group(id=123, name="Linked Label", index=0)
    next_group = Group(id=123, name="Linked Label", index=1)

    assert next(group) == next_group


def test_page(
    document_extraction: DocumentExtraction,
    form_extraction: FormExtraction,
    summarization: Summarization,
    unbundling: Unbundling,
) -> None:
    assert document_extraction.page == 0
    assert form_extraction.page == 0
    assert summarization.page == 0
    assert unbundling.pages == (0,)


@pytest.mark.parametrize(
    "prediction",
    ["document_extraction", "form_extraction", "summarization", "unbundling"],
)
def test_confidence(prediction: Prediction, request: object) -> None:
    prediction = request.getfixturevalue(prediction)  # type: ignore[ty:unresolved-attribute]
    prediction.confidence = 0.5
    assert prediction.confidence == 0.5
    assert prediction.to_dict()["confidence"][prediction.label] == 0.5


@pytest.mark.parametrize(
    "extraction",
    ["document_extraction", "form_extraction", "summarization"],
)
def test_accept(extraction: Extraction, request: object) -> None:
    extraction = request.getfixturevalue(extraction)  # type: ignore[ty:unresolved-attribute]
    changes = extraction.to_dict()
    assert "accepted" not in changes
    assert "rejected" not in changes

    extraction.reject()
    extraction.accept()
    assert extraction.accepted
    assert not extraction.rejected

    changes = extraction.to_dict()
    assert "accepted" in changes
    assert "rejected" not in changes
    assert changes["accepted"]

    extraction.unaccept()
    assert not extraction.accepted


@pytest.mark.parametrize(
    "extraction",
    ["document_extraction", "form_extraction", "summarization"],
)
def test_reject(extraction: Extraction, request: object) -> None:
    extraction = request.getfixturevalue(extraction)  # type: ignore[ty:unresolved-attribute]
    changes = extraction.to_dict()
    assert "accepted" not in changes
    assert "rejected" not in changes

    extraction.accept()
    extraction.reject()
    assert extraction.rejected
    assert not extraction.accepted

    changes = extraction.to_dict()
    assert "rejected" in changes
    assert "accepted" not in changes
    assert changes["rejected"]

    extraction.unreject()
    assert not extraction.rejected


@pytest.mark.parametrize(
    "extraction",
    ["document_extraction", "form_extraction"],
)
def test_text(extraction: Extraction, request: object) -> None:
    extraction = request.getfixturevalue(extraction)  # type: ignore[ty:unresolved-attribute]
    changes = extraction.to_dict()
    assert changes["text"] == "ORIGINAL_OCR"
    assert changes["normalized"]["text"] == "ORIGINAL_GENAI"
    assert changes["normalized"]["formatted"] == "NORMALIZED"

    extraction.text = "UPDATED"
    changes = extraction.to_dict()
    assert changes["text"] == "UPDATED"
    assert changes["normalized"]["text"] == "UPDATED"
    assert changes["normalized"]["formatted"] == "UPDATED"


def test_text_checkbox(form_extraction: FormExtraction) -> None:
    form_extraction.type = FormExtractionType.CHECKBOX
    form_extraction.checked = False
    changes = form_extraction.to_dict()
    assert changes["text"] == "Unchecked"
    assert changes["normalized"]["text"] == "Unchecked"
    assert changes["normalized"]["formatted"] == "Unchecked"
    assert not changes["normalized"]["structured"]["checked"]

    form_extraction.checked = True
    changes = form_extraction.to_dict()
    assert changes["text"] == "Checked"
    assert changes["normalized"]["text"] == "Checked"
    assert changes["normalized"]["formatted"] == "Checked"
    assert changes["normalized"]["structured"]["checked"]


def test_text_signature(form_extraction: FormExtraction) -> None:
    form_extraction.type = FormExtractionType.SIGNATURE
    form_extraction.signed = False
    changes = form_extraction.to_dict()
    assert changes["text"] == "ORIGINAL_OCR"
    assert changes["normalized"]["text"] == "ORIGINAL_GENAI"
    assert changes["normalized"]["formatted"] == "Unsigned"
    assert not changes["normalized"]["structured"]["signed"]

    form_extraction.signed = True
    changes = form_extraction.to_dict()
    assert changes["text"] == "ORIGINAL_OCR"
    assert changes["normalized"]["text"] == "ORIGINAL_GENAI"
    assert changes["normalized"]["formatted"] == "Signed"
    assert changes["normalized"]["structured"]["signed"]


def test_spans(document_extraction: DocumentExtraction) -> None:
    old_span = document_extraction.span
    new_span = replace(old_span, page=1)

    document_extraction.spans.append(new_span)
    assert document_extraction.span == old_span
    assert document_extraction.spans == [old_span, new_span]
    assert len(document_extraction.to_dict()["spans"]) == 2

    document_extraction.span = new_span
    assert document_extraction.span == new_span
    assert document_extraction.spans == [new_span]
    assert len(document_extraction.to_dict()["spans"]) == 1

    document_extraction.spans = []
    assert not document_extraction.span
    assert document_extraction.span == NULL_SPAN
    assert len(document_extraction.to_dict()["spans"]) == 0

    document_extraction.span = NULL_SPAN
    assert not document_extraction.spans
    assert not document_extraction.span
    assert document_extraction.span == NULL_SPAN
    assert len(document_extraction.to_dict()["spans"]) == 0


def test_citations(summarization: Summarization) -> None:
    old_citation = summarization.citation
    old_span = summarization.span
    assert old_citation.span == old_span

    new_span = replace(old_span, page=1)
    new_citation = replace(old_citation, start=0, span=new_span)
    old_citation_new_span = replace(old_citation, span=new_span)

    summarization.citations.append(new_citation)
    assert summarization.citations == [old_citation, new_citation]
    assert summarization.citation == old_citation
    assert summarization.spans == (old_span, new_span)
    assert summarization.span == old_span
    assert len(summarization.to_dict()["citations"]) == 2

    summarization.span = new_span
    assert summarization.citations == [old_citation_new_span]
    assert summarization.spans == (new_span,)
    assert summarization.span == new_span
    assert len(summarization.to_dict()["citations"]) == 1

    summarization.citations = [old_citation, new_citation]
    summarization.citation = new_citation
    assert summarization.citations == [new_citation]
    assert summarization.spans == (new_span,)
    assert summarization.span == new_span
    assert len(summarization.to_dict()["citations"]) == 1

    summarization.citations = []
    assert not summarization.citation
    assert summarization.citation == NULL_CITATION
    assert not summarization.span
    assert summarization.span == NULL_SPAN
    assert len(summarization.to_dict()["citations"]) == 0

    summarization.citation = NULL_CITATION
    assert not summarization.citations
    assert not summarization.citation
    assert summarization.citation == NULL_CITATION
    assert len(summarization.to_dict()["citations"]) == 0
