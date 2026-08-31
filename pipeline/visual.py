import re


_HTML_TAG_RE = re.compile(r"<(/?)(strong|em|b|i)>")


def parse_html_emphasis(marked_text):
    """Parse HTML emphasis tags (<strong>, <em>, <b>, <i>).

    Returns (clean_text, emphasis_map) where emphasis_map uses word indices.
    """
    level_stack = []
    emphasis_map = {}
    clean_parts = []
    word_idx = 0
    i = 0
    while i < len(marked_text):
        m = _HTML_TAG_RE.match(marked_text, i)
        if m:
            is_close = m.group(1) == "/"
            tag = m.group(2)
            level = "strong" if tag in ("strong", "b") else "em"
            if is_close:
                if level_stack and level_stack[-1] == level:
                    level_stack.pop()
            else:
                level_stack.append(level)
            i = m.end()
        elif marked_text[i] in (" ", "\n", "\t"):
            clean_parts.append(" ")
            i += 1
        else:
            j = i
            while j < len(marked_text) and marked_text[j] not in (" ", "\n", "\t") and not _HTML_TAG_RE.match(marked_text, j):
                j += 1
            word = marked_text[i:j]
            clean_parts.append(word)
            if level_stack:
                emphasis_map[word_idx] = level_stack[-1]
            word_idx += 1
            i = j
    clean_text = "".join(clean_parts).strip()
    clean_text = re.sub(r"  +", " ", clean_text)
    return clean_text, emphasis_map


def resolve_visual(scene):
    """Convierte una escena semántica en parámetros técnicos."""
    visual = scene.get("visual")
    if not visual or not isinstance(visual, dict):
        return scene

    parts = []
    if visual.get("subject"):
        parts.append(visual["subject"])
    if visual.get("action"):
        parts.append(visual["action"])
    if visual.get("mood"):
        parts.append(f"{visual['mood']} mood")
    parts.append("soft natural light, cinematic, photorealistic, high detail")
    scene["ai"] = ", ".join(parts)

    if not scene.get("motion"):
        vtype = visual.get("type", "")
        motion_map = {
            "object_closeup": "zoom-in",
            "human_reflection": "zoom-in",
            "wide_landscape": "zoom-out",
            "hands_detail": "zoom-in",
            "environment": "pan-right",
            "symbolic": "zoom-out",
        }
        scene["motion"] = motion_map.get(vtype, "zoom-in")

    emphasis_words = scene.get("emphasis")
    if emphasis_words and isinstance(emphasis_words, list):
        text = scene["text"]
        for word in emphasis_words:
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            text = pattern.sub(f"<strong>{word}</strong>", text)
        scene["text"] = text
        del scene["emphasis"]

    return scene
