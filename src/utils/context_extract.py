"""
Extract text from opportunity uploads: plain text, markdown, or image (OCR when available).
"""
import io
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

MAX_TEXT = 100_000
MAX_IMAGE_TEXT = 25_000

ALLOWED_TEXT = {".txt", ".md", ".text"}
ALLOWED_IMAGE = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def _ext(name: str) -> str:
    if not name or "." not in name:
        return ""
    return "." + name.rsplit(".", 1)[-1].lower()


def extract_text_from_upload(file_storage) -> str:
    """
    Read .txt / .md as UTF-8, or run OCR on images if Pillow + pytesseract are available.
    """
    if file_storage is None or not getattr(file_storage, "filename", None):
        return ""

    name = file_storage.filename or ""
    ext = _ext(name)

    try:
        raw = file_storage.read()
    except Exception as e:
        logger.error("Error reading upload: %s", e)
        return ""

    if not raw:
        return ""

    if ext in ALLOWED_TEXT or ext == "":
        return raw.decode("utf-8", errors="replace")[:MAX_TEXT].strip()

    if ext in ALLOWED_IMAGE:
        return _ocr_image_bytes(raw)[:MAX_IMAGE_TEXT].strip()

    logger.warning("Unsupported file type for context: %s", name)
    return ""


def _ocr_image_bytes(data: bytes) -> str:
    try:
        from PIL import Image
        import pytesseract
        if os.getenv("TESSERACT_CMD"):
            pytesseract.pytesseract.tesseract_cmd = os.environ["TESSERACT_CMD"]
    except ImportError:
        return (
            "[Image uploaded but OCR is not available on the server. "
            "Add opportunity details in the text box, or install Pillow, pytesseract, and the Tesseract binary.]"
        )

    try:
        im = Image.open(io.BytesIO(data))
        im = im.convert("RGB")
        text = pytesseract.image_to_string(im) or ""
        im.close()
        if not text.strip():
            return "[Image processed but no text was detected. Add details in the text area.]"
        return text
    except Exception as e:
        logger.warning("OCR failed: %s", e)
        return f"[Could not read image text. Paste details in the text box. ({e})]"


def build_salesforce_context(
    use_custom: bool,
    account_name: str,
    opportunity_text: str,
    file_storage,
) -> Optional[str]:
    if not use_custom:
        return None
    acc = (account_name or "").strip()
    otxt = (opportunity_text or "").strip()
    file_text = extract_text_from_upload(file_storage) if file_storage and getattr(
        file_storage, "filename", None
    ) else ""

    combined = otxt
    if file_text:
        combined = (combined + "\n\n" + file_text).strip() if combined else file_text

    if not acc and not combined:
        return None

    parts = []
    if acc:
        parts.append(f"Salesforce account (use in the narrative): {acc}")
    if combined:
        parts.append(
            "Opportunity / deal context (align your writing with this):\n" + combined[:50000]
        )
    if not parts:
        return None
    return "\n\n".join(parts)


def combined_opportunity_text(opportunity_text: str, file_storage) -> str:
    """
    Same text combination as in build_salesforce_context (opportunity field + file upload)
    for use in narrative generation without re-reading storage.
    """
    otxt = (opportunity_text or "").strip()
    file_text = (
        extract_text_from_upload(file_storage)
        if file_storage and getattr(file_storage, "filename", None)
        else ""
    )
    if not file_text:
        return otxt
    if not otxt:
        return file_text
    return (otxt + "\n\n" + file_text).strip()
