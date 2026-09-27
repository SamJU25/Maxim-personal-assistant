"""
Unit tests for DocumentReaderEngine, read_document, inspect_image, and FastAPI endpoints.
"""
import io
import json
import base64
import zipfile
import pytest
from pathlib import Path
from PIL import Image
from fastapi.testclient import TestClient

from document_reader import document_reader
from server import app

client = TestClient(app)

@pytest.fixture
def sample_vault(tmp_path: Path):
    """Sets up a temporary vault directory for document tests."""
    vault = tmp_path / "vault"
    vault.mkdir()
    document_reader.vault_dir = vault
    document_reader.attachments_dir = vault / "01 - Memory" / "Attachments"
    document_reader.attachments_dir.mkdir(parents=True, exist_ok=True)
    return vault

def test_read_text_and_markdown(sample_vault: Path):
    doc_path = sample_vault / "sample.txt"
    doc_path.write_text("Hello MaxIM, this is a plain text document.\nTesting reading capabilities.", encoding="utf-8")

    res = document_reader.read_document(str(doc_path))
    assert res["success"] is True
    assert "Hello MaxIM" in res["content"]
    assert res["metadata"]["extension"] == ".txt"

def test_read_csv(sample_vault: Path):
    csv_path = sample_vault / "data.csv"
    csv_path.write_text("Name,Role,Score\nAlice,Engineer,95\nBob,Designer,88", encoding="utf-8")

    res = document_reader.read_document(str(csv_path))
    assert res["success"] is True
    assert "| Name | Role | Score |" in res["content"]
    assert "| Alice | Engineer | 95 |" in res["content"]
    assert res["metadata"]["columns"] == 3
    assert res["metadata"]["total_rows"] == 3

def test_read_docx(sample_vault: Path):
    docx_path = sample_vault / "sample.docx"
    xml_content = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:body>'
        '<w:p><w:r><w:t>First Paragraph in Word Document</w:t></w:r></w:p>'
        '<w:p><w:r><w:t>Second Paragraph with more content</w:t></w:r></w:p>'
        '</w:body></w:document>'
    )
    with zipfile.ZipFile(docx_path, "w") as z:
        z.writestr("word/document.xml", xml_content.encode("utf-8"))

    res = document_reader.read_document(str(docx_path))
    assert res["success"] is True
    assert "First Paragraph in Word Document" in res["content"]
    assert "Second Paragraph with more content" in res["content"]
    assert res["metadata"]["paragraph_count"] == 2

def test_read_pdf(sample_vault: Path):
    import pypdf
    pdf_path = sample_vault / "sample.pdf"
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with open(pdf_path, "wb") as f:
        writer.write(f)

    res = document_reader.read_document(str(pdf_path))
    assert res["success"] is True
    assert res["metadata"]["extension"] == ".pdf"
    assert res["metadata"]["page_count"] == 1

@pytest.mark.asyncio
async def test_inspect_image(sample_vault: Path):
    img_path = sample_vault / "test_pic.png"
    img = Image.new("RGB", (320, 240), color=(255, 128, 64))
    img.save(img_path, format="PNG")

    res = await document_reader.inspect_image(str(img_path), prompt="What size is this?")
    assert res["success"] is True
    assert res["dimensions"]["width"] == 320
    assert res["dimensions"]["height"] == 240
    assert res["format"] == "PNG"
    assert res["color_mode"] == "RGB"
    assert "test_pic.png" in res["visual_description"]

def test_file_not_found():
    res = document_reader.read_document("non_existent_file_12345.pdf")
    assert res["success"] is False
    assert "not found" in res["error"].lower()

def test_save_attachments(sample_vault: Path):
    # Base64 data URL
    data = base64.b64encode(b"dummy image bytes").decode("utf-8")
    data_url = f"data:image/png;base64,{data}"

    saved_path = document_reader.save_attachment_base64("upload.png", data_url)
    assert saved_path.exists()
    assert saved_path.read_bytes() == b"dummy image bytes"

def test_api_endpoints(sample_vault: Path):
    doc_path = sample_vault / "api_test.txt"
    doc_path.write_text("API test content for document reader", encoding="utf-8")

    # Read Document Endpoint
    resp = client.post("/api/document/read", json={"file_path": str(doc_path)})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "API test content" in data["content"]

    # Inspect Image Endpoint
    img_path = sample_vault / "api_test.png"
    img = Image.new("RGB", (100, 100), color=(0, 200, 100))
    img.save(img_path, format="PNG")

    resp_img = client.post("/api/image/inspect", json={"image_path": str(img_path)})
    assert resp_img.status_code == 200
    img_data = resp_img.json()
    assert img_data["success"] is True
    assert img_data["dimensions"]["width"] == 100
