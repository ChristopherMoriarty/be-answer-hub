from urllib.parse import quote


def _ascii_fallback_filename(filename: str) -> str:
    """Keep readable Latin/ASCII parts for legacy Content-Disposition clients."""
    cleaned = "".join(
        ch if 32 <= ord(ch) < 127 and ch not in ('"', "\\") else " " for ch in filename
    )
    cleaned = " ".join(cleaned.split())
    if not cleaned or not any(ch.isalnum() for ch in cleaned):
        return "cv.pdf"
    return cleaned


def build_content_disposition(filename: str, *, inline: bool) -> str:
    """Build a Content-Disposition header for PDF responses."""
    disposition = "inline" if inline else "attachment"
    ascii_fallback = _ascii_fallback_filename(filename)
    encoded = quote(filename, safe="")
    return f"{disposition}; filename=\"{ascii_fallback}\"; filename*=UTF-8''{encoded}"


def build_inline_content_disposition(filename: str) -> str:
    """Build a Content-Disposition header for inline PDF preview."""
    return build_content_disposition(filename, inline=True)


def build_attachment_content_disposition(filename: str) -> str:
    """Build a Content-Disposition header for PDF download."""
    return build_content_disposition(filename, inline=False)
