from io import BytesIO
import pytest
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
from backend.documents import parse, DocumentError
from backend.worker import ingest_document
from tests.conftest import library

pytestmark = pytest.mark.asyncio(loop_scope="session")


def pdf_fixture(text=None):
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    if text:
        font = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
        page[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
        )
        stream = DecodedStreamObject()
        stream.set_data(("BT /F1 12 Tf 72 720 Td (" + text + ") Tj ET").encode())
        page[NameObject("/Contents")] = writer._add_object(stream)
    result = BytesIO()
    writer.write(result)
    return result.getvalue()


async def test_pdf_upload_extracts_page_provenance(client):
    kb = await library(client)
    content = pdf_fixture("Reference documents support PDF uploads.")
    response = await client.post(
        "/api/v1/documents", data={"kb_id": kb}, files={"file": ("reference.pdf", content, "application/pdf")}
    )
    assert response.status_code == 202
    identifier = response.json()["id"]
    await ingest_document({}, identifier)
    source = (await client.get("/api/v1/documents/" + identifier + "/source")).json()
    assert source["document"]["status"] == "indexed"
    assert source["passages"][0]["page"] == 1
    assert "Reference documents support PDF uploads." in source["passages"][0]["text"]


async def test_empty_pdf_is_explicitly_needs_ocr():
    with pytest.raises(DocumentError, match="needs_ocr"):
        parse(pdf_fixture(), ".pdf", "scan.pdf")
