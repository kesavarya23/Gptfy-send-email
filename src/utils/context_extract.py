"""
Extract text from opportunity uploads: plain text, markdown, or image.

Image OCR runs in two stages and silently falls through to the next on failure:
  1. Local Tesseract via pytesseract (free, fast, works offline).
  2. OpenAI vision model (uses ``OPENAI_API_KEY`` already configured for the
     AI email writer; defaults to ``OPENAI_VISION_MODEL`` → ``OPENAI_MODEL`` →
     ``gpt-4o-mini``). Lets the app extract text from screenshots on hosts
     that don't ship the Tesseract binary (e.g. Vercel).

If both fail the function returns ``""`` so the ``/send_emails`` handler can
show its friendly "could not read text from your image" message instead of
embedding raw OCR error strings into the generated email.
"""
import base64
import io
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

MAX_TEXT = 100_000
MAX_IMAGE_TEXT = 25_000

ALLOWED_TEXT = {".txt", ".md", ".text"}
ALLOWED_IMAGE = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

_EXT_TO_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}

_DEFAULT_VISION_MODEL = "gpt-4o-mini"
_DEFAULT_VISION_TIMEOUT = 30.0


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
    Read .txt / .md as UTF-8, or extract text from an image upload.

    Image uploads first try local Tesseract; if it isn't installed or returns
    nothing, the OpenAI vision model is used as a fallback (when
    OPENAI_API_KEY is set). See module docstring for details.
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
        mime = _EXT_TO_MIME.get(ext, "image/png")
        out = _ocr_image_bytes(raw, mime=mime)[:MAX_IMAGE_TEXT].strip()
        _rewind(file_storage)
        return out

    logger.warning("Unsupported file type for context: %s", name)
    _rewind(file_storage)
    return ""


def _ocr_image_bytes(data: bytes, mime: str = "image/png") -> str:
    """
    Return extracted text from a screenshot, or empty string on total failure.

    Tries the local Tesseract path first (free, offline). When that yields no
    text — typically because the binary isn't installed on the host or the
    image is hard to read — falls back to an OpenAI vision call using the
    same API key as the email writer. Both layers swallow their own errors so
    we never embed OCR / Tesseract / API error strings into the generated email.
    """
    text = _tesseract_ocr(data)
    if text:
        return text
    vision = _openai_vision_ocr(data, mime)
    if vision:
        return vision
    logger.info(
        "OCR returned no text from image; user should add details in the text area."
    )
    return ""


def _tesseract_ocr(data: bytes) -> str:
    """Local Tesseract OCR. Returns '' if the binary or libs are unavailable."""
    try:
        from PIL import Image
        import pytesseract
        if os.getenv("TESSERACT_CMD"):
            pytesseract.pytesseract.tesseract_cmd = os.environ["TESSERACT_CMD"]
    except ImportError:
        logger.info(
            "Tesseract OCR unavailable (PIL/pytesseract not installed); "
            "will try OpenAI vision fallback if configured."
        )
        return ""

    try:
        im = Image.open(io.BytesIO(data))
        im = im.convert("RGB")
        text = pytesseract.image_to_string(im) or ""
        im.close()
        return text.strip()
    except Exception as e:
        logger.info(
            "Tesseract OCR failed (%s); will try OpenAI vision fallback if configured.",
            e,
        )
        return ""


def _vision_model() -> str:
    """Resolve the OpenAI model used for vision OCR."""
    return (
        (os.getenv("OPENAI_VISION_MODEL") or "").strip()
        or (os.getenv("OPENAI_MODEL") or "").strip()
        or _DEFAULT_VISION_MODEL
    )


def _openai_vision_ocr(data: bytes, mime: str) -> str:
    """
    Last-resort OCR using the configured OpenAI vision model.

    Returns "" when the API key is missing, the openai package isn't installed,
    or any error occurs. Never raises — silent failure preserves the existing
    UX (the user gets the friendly "could not read your image" error from the
    /send_emails handler).
    """
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        return ""

    try:
        from openai import OpenAI
    except ImportError:
        logger.warning("Vision OCR skipped: 'openai' package not installed.")
        return ""

    if mime not in {"image/png", "image/jpeg", "image/gif", "image/webp"}:
        mime = "image/png"

    try:
        b64 = base64.b64encode(data).decode("ascii")
    except Exception as e:
        logger.warning("Vision OCR base64 encode failed: %s", e)
        return ""

    try:
        timeout = float(os.getenv("OPENAI_TIMEOUT") or _DEFAULT_VISION_TIMEOUT)
    except (TypeError, ValueError):
        timeout = _DEFAULT_VISION_TIMEOUT

    system_prompt = (
        "You are an OCR + light extraction assistant. Transcribe every readable "
        "Salesforce / CRM fact visible in the screenshot. Output PLAIN TEXT only "
        "(no markdown, no commentary, no preamble). When you can identify them, "
        "put fields like Account, Opportunity, Stage, Amount, Close Date, Owner, "
        "Probability, Next Step on their own lines as 'Field: value'. Otherwise "
        "output the raw transcribed text verbatim. Never invent values that are "
        "not visible in the image."
    )

    try:
        client = OpenAI(api_key=api_key, timeout=timeout)
        resp = client.chat.completions.create(
            model=_vision_model(),
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Transcribe this screenshot."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{b64}"},
                        },
                    ],
                },
            ],
        )
        text = (resp.choices[0].message.content or "").strip()
        if text:
            logger.info(
                "Vision OCR extracted %d chars from screenshot using %s.",
                len(text),
                _vision_model(),
            )
        return text
    except Exception as e:
        logger.warning("Vision OCR failed: %s", e)
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
