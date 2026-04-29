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


def _rewind(file_storage) -> None:
    try:
        if file_storage and hasattr(file_storage, "seek"):
            file_storage.seek(0)
    except Exception:
        pass


def is_uploaded_file_without_extractable_text(
    file_storage,
    account_name: str,
    opportunity_text: str,
) -> bool:
    """
    True if user attached a file, did not type account or opportunity in the form,
    and we could not extract any text (e.g. no OCR on server). The UI should show an
    error — do not use this in email body.
    """
    if not file_storage or not getattr(file_storage, "filename", None) or not (
        (file_storage.filename or "").strip()
    ):
        return False
    if (account_name or "").strip() or (opportunity_text or "").strip():
        return False
    extracted = extract_text_from_upload(file_storage)
    return not (extracted and extracted.strip())


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
        _rewind(file_storage)
        return ""

    if not raw:
        _rewind(file_storage)
        return ""

    if ext in ALLOWED_TEXT or ext == "":
        out = raw.decode("utf-8", errors="replace")[:MAX_TEXT].strip()
        _rewind(file_storage)
        return out

    if ext in ALLOWED_IMAGE:
        # Never inject technical/OCR error strings into email context (use text area instead).
        out = _ocr_image_bytes(raw)[:MAX_IMAGE_TEXT].strip()
        _rewind(file_storage)
        return out

    logger.warning("Unsupported file type for context: %s", name)
    _rewind(file_storage)
    return ""


def _ocr_image_bytes(data: bytes) -> str:
    """
    Return extracted text or empty string. On failure, return "" so the UI text box
    (Account / Opportunity details) remains the only source of truth—never embed
    Tesseract error messages into generated emails.
    """
    try:
        from PIL import Image
        import pytesseract
        if os.getenv("TESSERACT_CMD"):
            pytesseract.pytesseract.tesseract_cmd = os.environ["TESSERACT_CMD"]
    except ImportError:
        logger.warning(
            "OCR skipped: PIL/pytesseract not available. Add opportunity text manually or install OCR."
        )
        return ""

    try:
        im = Image.open(io.BytesIO(data))
        im = im.convert("RGB")
        text = pytesseract.image_to_string(im) or ""
        im.close()
        if not text.strip():
            logger.info("OCR returned no text from image; user should add details in the text area.")
            return ""
        return text
    except Exception as e:
        logger.warning("OCR failed: %s", e)
        return ""


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
    has_file = bool(
        file_storage
        and getattr(file_storage, "filename", None)
        and (file_storage.filename or "").strip()
    )
    file_text = (
        extract_text_from_upload(file_storage) if has_file else ""
    )

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
    has_file = bool(
        file_storage
        and getattr(file_storage, "filename", None)
        and (file_storage.filename or "").strip()
    )
    file_text = extract_text_from_upload(file_storage) if has_file else ""
    if not file_text:
        return otxt
    if not otxt:
        return file_text
    return (otxt + "\n\n" + file_text).strip()
