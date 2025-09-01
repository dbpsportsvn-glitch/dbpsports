from django import template
import re

register = template.Library()

_YT_ID = re.compile(r"(?:v=|youtu\.be/|embed/|shorts/|/live/)([0-9A-Za-z_-]{11})")

@register.filter
def yt_embed_clean(url: str) -> str:
    if not url:
        return ""
    m = _YT_ID.search(url)
    vid = m.group(1) if m else ""
    return f"https://www.youtube-nocookie.com/embed/{vid}" if vid else ""
