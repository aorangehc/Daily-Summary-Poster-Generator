from typing import List, Tuple
from PIL import Image, ImageDraw

from core.theme import THEMES, DEFAULT_THEME_ID
from core.fonts import get_font
from modules.base import BaseModule
from modules.title import TitleModule
from modules.summary import SummaryModule
from modules.stats import StatsModule
from modules.quote import QuoteModule
from modules.rich import RichModule
from modules.image import ImageModule


def _rounded_rect(draw: ImageDraw.ImageDraw, xy, radius: int, fill=None, outline=None, width: int = 1):
    try:
        draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)
    except Exception:
        # fallback: simple rectangle
        draw.rectangle(xy, fill=fill, outline=outline, width=width)


def _text_wh(draw: ImageDraw.ImageDraw, text: str, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _text_w(draw: ImageDraw.ImageDraw, text: str, font):
    w, _ = _text_wh(draw, text, font)
    return w


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int):
    if not text:
        return []
    lines = []
    line = ""
    # Simple mixed CJK/latin wrap: prefer split on whitespace, else char-wise
    for token in _tokenize_text(text):
        test = line + token
        w = _text_w(draw, test, font)
        if w <= max_width:
            line = test
        else:
            if line:
                lines.append(line.rstrip())
            # if single token already too long, force split by char
            if _text_w(draw, token, font) > max_width:
                for ch in token:
                    test2 = ("" if not line else line) + ch
                    w2 = _text_w(draw, test2, font)
                    if w2 <= max_width:
                        line = test2
                    else:
                        if line:
                            lines.append(line)
                        line = ch
            else:
                line = token
    if line:
        lines.append(line.rstrip())
    return lines


def _tokenize_text(text: str):
    buf = ""
    for ch in text:
        if ch.isspace():
            if buf:
                yield buf
                buf = ""
            yield ch
        elif _is_cjk(ch):
            if buf:
                yield buf
                buf = ""
            yield ch
        else:
            buf += ch
    if buf:
        yield buf


def _is_cjk(char: str) -> bool:
    code = ord(char)
    return (
        0x4E00 <= code <= 0x9FFF
        or 0x3400 <= code <= 0x4DBF
        or 0x20000 <= code <= 0x2A6DF
        or 0x2A700 <= code <= 0x2B73F
        or 0x2B740 <= code <= 0x2B81F
        or 0x2B820 <= code <= 0x2CEAF
        or 0xF900 <= code <= 0xFAFF
        or 0x2F800 <= code <= 0x2FA1F
    )


def render_poster(
    modules: List[BaseModule],
    theme_id: str = DEFAULT_THEME_ID,
    width: int = 1240,
    height: int = 1754,
    padding: int = 64,
    scale: float = 1.0,
):
    theme = THEMES.get(theme_id, THEMES[DEFAULT_THEME_ID])
    pal = theme["palette"]
    tok = theme["tokens"]

    sw, sh = int(width * scale), int(height * scale)
    pad = int(padding * scale)
    img = Image.new("RGB", (sw, sh), pal.get("background", "#ffffff"))
    # Background gradient (optional)
    bg_grad = theme.get("background_gradient")
    if bg_grad:
        _fill_gradient(img, (0, 0, sw, sh), bg_grad.get("start"), bg_grad.get("end"), int(bg_grad.get("angle", 90)))
    draw = ImageDraw.Draw(img)

    x0, y = pad, pad
    content_w = sw - 2 * pad
    gap = int(tok["gap"] * scale)
    radius = int(tok["radius"] * scale)
    card_pad = int(tok["card_padding"] * scale)

    # Title area top spacing
    for m in modules:
        # Module card
        # card background
        card_h = _render_module(
            img=img,
            draw=draw,
            module=m,
            pal=pal,
            tok=tok,
            scale=scale,
            area=(x0, y, x0 + content_w, sh - pad),
            radius=radius,
            card_pad=card_pad,
        )
        y += card_h + gap

    return img


def _render_module(img: Image.Image, draw: ImageDraw.ImageDraw, module: BaseModule, pal: dict, tok: dict, scale: float, area: Tuple[int, int, int, int], radius: int, card_pad: int) -> int:
    x1, y1, x2, y2 = area
    box_w = x2 - x1
    # Temporary large height; we will compute content height and then draw card
    inner_x1 = x1 + card_pad
    inner_y = y1 + card_pad
    inner_w = box_w - 2 * card_pad

    # collect drawing calls on a temporary overlay to measure height accurately
    lines = []  # (callable)
    text_color = pal.get("text", "#222222")

    # Resolve style overrides
    style = getattr(module, "style", {}) or {}
    card_fill = style.get("bg_color") or pal.get("card")
    card_outline = pal.get("card_border")
    card_radius = int(style.get("radius", radius))
    card_padding = int(style.get("padding", card_pad))
    inner_x1 = x1 + card_padding
    inner_y = y1 + card_padding
    inner_w = box_w - 2 * card_padding
    text_color = style.get("text_color") or pal.get("text", "#222222")
    accent_color = style.get("accent_color") or pal.get("primary", text_color)
    card_gradient = style.get("bg_gradient")  # {start,end,angle}

    # Title Module
    if isinstance(module, TitleModule):
        title_font = get_font(int(42 * scale), bold=True)
        sub_font = get_font(int(20 * scale))
        align = module.align or "left"
        # wrap title
        title_lines = _wrap_text(draw, module.title or "", title_font, inner_w)
        sub_lines = _wrap_text(draw, module.subtitle or "", sub_font, inner_w)
        lh_title = title_font.size + int(10 * scale)
        lh_sub = sub_font.size + int(6 * scale)
        h = card_padding + len(title_lines) * lh_title + (int(8 * scale) if sub_lines else 0) + len(sub_lines) * lh_sub + card_padding

        # draw card (gradient or solid)
        _draw_card(img, (x1, y1, x2, y1 + h), card_radius, card_fill, card_outline, card_gradient)
        cy = inner_y
        for line in title_lines:
            w = _text_w(draw, line, title_font)
            if align == "center":
                cx = inner_x1 + (inner_w - w) // 2
            else:
                cx = inner_x1
            draw.text((cx, cy), line, fill=text_color, font=title_font)
            cy += lh_title
        if sub_lines:
            cy += int(8 * scale)
            for line in sub_lines:
                w = _text_w(draw, line, sub_font)
                cx = inner_x1 if align != "center" else inner_x1 + (inner_w - w) // 2
                draw.text((cx, cy), line, fill=pal.get("muted", text_color), font=sub_font)
                cy += lh_sub
        return h

    # Summary Module
    if isinstance(module, SummaryModule):
        title_font = get_font(int(22 * scale), bold=True)
        body_font = get_font(int(18 * scale))
        bullet_gap = int(8 * scale)
        line_gap = int(8 * scale)
        header_h = 0
        if module.title:
            header_h = title_font.size + line_gap
        # Estimate height
        y_cursor = inner_y + header_h
        for item in module.items:
            # bullet + text
            bullet_w = _text_w(draw, module.bullet or "•", body_font)
            available_w = inner_w - bullet_w - bullet_gap
            for _line in _wrap_text(draw, str(item), body_font, available_w):
                y_cursor += body_font.size + line_gap
        h = (y_cursor - y1) + card_padding

        _draw_card(img, (x1, y1, x2, y1 + h), card_radius, card_fill, card_outline, card_gradient)
        cy = inner_y
        if module.title:
            draw.text((inner_x1, cy), module.title, fill=text_color, font=title_font)
            cy += header_h
        for item in module.items:
            bullet = module.bullet or "•"
            b_w = _text_w(draw, bullet, body_font)
            cx = inner_x1
            draw.text((cx, cy), bullet, fill=accent_color, font=body_font)
            cx += b_w + bullet_gap
            for line in _wrap_text(draw, str(item), body_font, inner_w - b_w - bullet_gap):
                draw.text((cx, cy), line, fill=text_color, font=body_font)
                cy += body_font.size + line_gap
        return h

    # Stats Module
    if isinstance(module, StatsModule):
        title_font = get_font(int(22 * scale), bold=True)
        label_font = get_font(int(14 * scale))
        value_font = get_font(int(24 * scale), bold=True)
        col_gap = int(16 * scale)
        row_gap = int(12 * scale)
        columns = max(1, min(4, int(module.columns or 2)))
        header_h = 0
        if module.title:
            header_h = title_font.size + int(10 * scale)
        cell_w = (inner_w - (columns - 1) * col_gap) // columns
        # one line per metric value + label
        rows = (len(module.metrics) + columns - 1) // columns
        cell_h = value_font.size + label_font.size + int(10 * scale)
        h = card_padding + header_h + rows * cell_h + (rows - 1) * row_gap + card_padding
        _draw_card(img, (x1, y1, x2, y1 + h), card_radius, card_fill, card_outline, card_gradient)

        cy = inner_y
        if module.title:
            draw.text((inner_x1, cy), module.title, fill=text_color, font=title_font)
            cy += header_h
        # grid
        start_y = cy
        for idx, metric in enumerate(module.metrics):
            r = idx // columns
            c = idx % columns
            cx = inner_x1 + c * (cell_w + col_gap)
            cy = start_y + r * (cell_h + row_gap)
            # value
            draw.text((cx, cy), str(metric.get("value", "")), fill=accent_color, font=value_font)
            cy += value_font.size + int(2 * scale)
            draw.text((cx, cy), str(metric.get("label", "")), fill=pal.get("muted", text_color), font=label_font)
        return h

    # Quote Module
    if isinstance(module, QuoteModule):
        quote_font = get_font(int(22 * scale))
        author_font = get_font(int(16 * scale))
        # measure
        lines = _wrap_text(draw, module.text or "", quote_font, inner_w)
        lh = quote_font.size + int(8 * scale)
        ah = author_font.size
        h = card_padding + len(lines) * lh + int(6 * scale) + ah + card_padding
        _draw_card(img, (x1, y1, x2, y1 + h), card_radius, card_fill, card_outline, card_gradient)
        cy = inner_y
        for line in lines:
            draw.text((inner_x1, cy), line, fill=text_color, font=quote_font)
            cy += lh
        cy += int(6 * scale)
        author = module.author or ""
        if author:
            draw.text((inner_x1, cy), f"— {author}", fill=pal.get("muted", text_color), font=author_font)
        return h

    # Rich Module (customizable)
    if isinstance(module, RichModule):
        title_font = get_font(int(24 * scale), bold=True)
        body_font = get_font(int(18 * scale))
        line_gap = int(8 * scale)
        header_h = 0
        if module.title:
            header_h = title_font.size + int(8 * scale)
        cy = inner_y + header_h
        # estimate body
        h = card_padding + header_h
        if module.body:
            for _line in _wrap_text(draw, module.body, body_font, inner_w):
                h += body_font.size + line_gap
        if module.items:
            h += int(8 * scale)
            for it in module.items:
                for _line in _wrap_text(draw, it, body_font, inner_w):
                    h += body_font.size + line_gap
        # image height if provided
        img_h = 0
        if getattr(module, "image_path", None):
            try:
                from PIL import Image

                im = Image.open(module.image_path)
                # fit width, keep aspect, target height up to 240
                max_h = int(240 * scale)
                ratio = min(inner_w / im.width, max_h / im.height)
                img_h = int(im.height * ratio)
            except Exception:
                img_h = 0
        h += img_h + card_padding

        _draw_card(img, (x1, y1, x2, y1 + h), card_radius, card_fill, card_outline, card_gradient)
        cy = inner_y
        if module.title:
            draw.text((inner_x1, cy), module.title, fill=text_color, font=title_font)
            cy += header_h
        if module.body:
            for line in _wrap_text(draw, module.body, body_font, inner_w):
                draw.text((inner_x1, cy), line, fill=text_color, font=body_font)
                cy += body_font.size + line_gap
        if module.items:
            cy += int(8 * scale)
            for it in module.items:
                for line in _wrap_text(draw, it, body_font, inner_w):
                    draw.text((inner_x1, cy), line, fill=text_color, font=body_font)
                    cy += body_font.size + line_gap
        if getattr(module, "image_path", None):
            try:
                from PIL import Image

                im = Image.open(module.image_path).convert("RGBA")
                ratio = min(inner_w / im.width, (img_h or 1) / im.height)
                im = im.resize((int(im.width * ratio), int(im.height * ratio)))
                img.paste(im, (inner_x1, cy), mask=im)
            except Exception:
                pass
        return h

    # Image/Sticker Module
    if isinstance(module, ImageModule):
        # reserve fixed height
        h = card_padding + module.height + card_padding
        _draw_card(img, (x1, y1, x2, y1 + h), card_radius, card_fill, card_outline, card_gradient)
        try:
            from PIL import Image

            im = Image.open(module.path).convert("RGBA")
            # fit by height
            ratio = module.height / im.height if im.height else 1
            new_w, new_h = int(im.width * ratio), int(im.height * ratio)
            if module.fit == "cover" and new_w < inner_w:
                # scale to cover width
                ratio = inner_w / im.width
                new_w, new_h = int(im.width * ratio), int(im.height * ratio)
            im = im.resize((min(new_w, inner_w), min(new_h, module.height)))
            img_w, img_h = im.size
            # center horizontally
            cx = inner_x1 + max(0, (inner_w - img_w) // 2)
            cy = inner_y + max(0, (module.height - img_h) // 2)
            img.paste(im, (cx, cy), mask=im)
        except Exception:
            pass
        return h

    # default fallback: empty block height
    h = int(80 * scale)
    _draw_card(img, (x1, y1, x2, y1 + h), card_radius, card_fill, card_outline, card_gradient)
    return h


def _draw_card(img: Image.Image, rect, radius: int, fill_color: str, outline_color: str, gradient: dict | None):
    x1, y1, x2, y2 = rect
    w, h = x2 - x1, y2 - y1
    if w <= 0 or h <= 0:
        return
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if gradient and gradient.get("start") and gradient.get("end"):
        _fill_gradient(overlay, (0, 0, w, h), gradient["start"], gradient["end"], int(gradient.get("angle", 90)))
    else:
        ImageDraw.Draw(overlay).rectangle((0, 0, w, h), fill=fill_color or "#ffffff")
    # rounded mask
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    try:
        md.rounded_rectangle((0, 0, w, h), radius=radius, fill=255)
    except Exception:
        md.rectangle((0, 0, w, h), fill=255)
    # apply
    img.paste(overlay, (x1, y1), mask)
    # outline
    if outline_color:
        d = ImageDraw.Draw(img)
        try:
            d.rounded_rectangle((x1, y1, x2, y2), radius=radius, outline=outline_color, width=1)
        except Exception:
            d.rectangle((x1, y1, x2, y2), outline=outline_color, width=1)


def _fill_gradient(target: Image.Image, rect, start_color: str, end_color: str, angle: int):
    # Only vertical(90) or horizontal(0/180) gradients supported for simplicity
    x1, y1, x2, y2 = rect
    w, h = x2 - x1, y2 - y1
    if w <= 0 or h <= 0:
        return
    start = _hex_to_rgb(start_color)
    end = _hex_to_rgb(end_color)
    horiz = abs(((angle % 360) + 360) % 360) in (0, 180)
    base = Image.new("RGBA", (w, h))
    dr = end[0] - start[0]
    dg = end[1] - start[1]
    db = end[2] - start[2]
    if horiz:
        for x in range(w):
            t = x / max(1, w - 1)
            col = (int(start[0] + dr * t), int(start[1] + dg * t), int(start[2] + db * t), 255)
            ImageDraw.Draw(base).line([(x, 0), (x, h)], fill=col)
    else:
        for y in range(h):
            t = y / max(1, h - 1)
            col = (int(start[0] + dr * t), int(start[1] + dg * t), int(start[2] + db * t), 255)
            ImageDraw.Draw(base).line([(0, y), (w, y)], fill=col)
    # paste to target
    target.paste(base, (x1, y1))


def _hex_to_rgb(h: str):
    hs = h.strip().lstrip('#')
    if len(hs) == 3:
        hs = ''.join([c * 2 for c in hs])
    r = int(hs[0:2], 16)
    g = int(hs[2:4], 16)
    b = int(hs[4:6], 16)
    return (r, g, b)
