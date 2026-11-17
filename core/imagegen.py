from __future__ import annotations

import io
from typing import Callable, Optional

from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ── palette (Modern Glassmorphism V4) ───────────────────────────────

BG_A = (10, 11, 18)       # Deep immersive dark navy
BG_B = (22, 16, 38)       # Rich cosmic purple tint
GRID_DOT = (255, 255, 255, 12)
CARD_FILL = (255, 255, 255, 12)       # Slightly richer glass transparency
CARD_BORDER = (255, 255, 255, 50)     # Crisper glass edge outline
MUTED = (160, 163, 184)
WHITE = (245, 246, 252)

# Vibrant Accent Tones
BLURPLE = (99, 102, 241)  # Indigo / Modern Blurple
GREEN = (74, 222, 128)    # Emerald Mint
YELLOW = (250, 204, 21)   # Amber Gold
RED = (248, 113, 113)     # Coral Rose
PINK = (244, 114, 182)    # Neon Rose Pink


# ── low-level helpers ────────────────────────────────────────────────


def _font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _text_w(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def _diagonal_gradient(size: tuple[int, int], a: tuple[int, int, int], b: tuple[int, int, int]) -> Image.Image:
    w, h = size
    base = Image.new("RGB", (w, h))
    px = base.load()
    diag = w + h
    for y in range(h):
        for x in range(0, w, 4):
            t = (x + y) / diag
            r = round(a[0] + (b[0] - a[0]) * t)
            g = round(a[1] + (b[1] - a[1]) * t)
            bl = round(a[2] + (b[2] - a[2]) * t)
            for dx in range(4):
                if x + dx < w:
                    px[x + dx, y] = (r, g, bl)
    return base


def _dot_grid(size: tuple[int, int], spacing: int = 28) -> Image.Image:
    w, h = size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for y in range(0, h, spacing):
        for x in range(0, w, spacing):
            draw.ellipse([x, y, x + 2, y + 2], fill=GRID_DOT)
    return layer


def _glow_blob(size: tuple[int, int], center: tuple[int, int], radius: int, color: tuple[int, int, int], alpha: int = 150) -> Image.Image:
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.ellipse(
        [center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius],
        fill=(*color, alpha),
    )
    return layer.filter(ImageFilter.GaussianBlur(radius // 2))


def _rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (size[0] - 1, size[1] - 1)], radius=radius, fill=255)
    return mask


def _overlay(canvas: Image.Image, draw_fn: Callable[[ImageDraw.ImageDraw], None]) -> Image.Image:
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(layer))
    return Image.alpha_composite(canvas, layer)


def _base_canvas(w: int, h: int, glow_color: tuple[int, int, int] = BLURPLE) -> Image.Image:
    bg = _diagonal_gradient((w, h), BG_A, BG_B).convert("RGBA")
    bg.alpha_composite(_glow_blob((w, h), (int(w * 0.15), int(h * 0.12)), int(min(w, h) * 0.55), glow_color, alpha=80))
    bg.alpha_composite(_glow_blob((w, h), (int(w * 0.88), int(h * 0.9)), int(min(w, h) * 0.45), PINK, alpha=50))
    bg.alpha_composite(_dot_grid((w, h)))
    return bg


def _glass_card(size: tuple[int, int], radius: int = 36) -> Image.Image:
    w, h = size
    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    mask = _rounded_mask((w, h), radius)
    fill_layer = Image.new("RGBA", (w, h), CARD_FILL)
    card.paste(fill_layer, (0, 0), mask)
    ImageDraw.Draw(card).rounded_rectangle([(1, 1), (w - 2, h - 2)], radius=radius, outline=CARD_BORDER, width=2)
    return card


def _pill(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font, fg, bg, pad_x: int = 16, pad_y: int = 7) -> int:
    x, y = xy
    tw = _text_w(draw, text, font)
    box = [x, y, x + tw + pad_x * 2, y + pad_y * 2 + font.size]
    draw.rounded_rectangle(box, radius=(box[3] - box[1]) // 2, fill=bg)
    draw.text((x + pad_x, y + pad_y - 1), text, font=font, fill=fg)
    return box[2] - box[0]


def _dot(draw: ImageDraw.ImageDraw, xy: tuple[int, int], radius: int, color) -> None:
    x, y = xy
    draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color)


def _to_bytes(img: Image.Image) -> io.BytesIO:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf


def _latency_tier(ms: int) -> tuple[tuple[int, int, int], str]:
    if ms < 100:
        return GREEN, "EXCELLENT"
    if ms < 200:
        return YELLOW, "OKAY"
    return RED, "POOR"


# ── PING: gradient ring gauge (Static PNG) ──────────────────────────


def render_ping_gauge(ws_ms: int, api_ms: Optional[int] = None) -> io.BytesIO:
    w, h = 760, 540
    color, tier_label = _latency_tier(ws_ms)
    canvas = _base_canvas(w, h, glow_color=color)

    card_margin = 24
    canvas.alpha_composite(_glass_card((w - card_margin * 2, h - card_margin * 2), radius=38), (card_margin, card_margin))

    draw = ImageDraw.Draw(canvas)
    title_font = _font(24)
    draw.text((card_margin + 36, card_margin + 30), "NETWORK LATENCY", font=title_font, fill=WHITE)
    
    pill_font = _font(15)
    _pill(draw, (w - card_margin - 160, card_margin + 26), tier_label, pill_font, (15, 23, 42), color, pad_x=16, pad_y=7)

    cx, cy, r = w // 2, h // 2 + 10, 135
    thickness = 24
    track_box = [cx - r, cy - r, cx + r, cy + r]
    start_angle = 90
    sweep_max = 300
    capped = max(0, min(ws_ms, 300))
    sweep = (capped / 300) * sweep_max

    canvas = _overlay(canvas, lambda d: d.arc(track_box, start_angle, start_angle + sweep_max, fill=(255, 255, 255, 30), width=thickness))
    canvas = _overlay(canvas, lambda d: d.arc(track_box, start_angle, start_angle + sweep, fill=(*color, 50), width=thickness + 16))
    canvas = _overlay(canvas, lambda d: d.arc(track_box, start_angle, start_angle + sweep, fill=(*color, 100), width=thickness + 6))

    draw = ImageDraw.Draw(canvas)
    if sweep > 0:
        draw.arc(track_box, start_angle, start_angle + sweep, fill=color, width=thickness)

    big_font = _font(64)
    unit_font = _font(20)
    label_font = _font(16)

    value_text = f"{ws_ms}"
    tw = _text_w(draw, value_text, big_font)
    draw.text((cx - tw / 2 - 14, cy - 50), value_text, font=big_font, fill=WHITE)
    draw.text((cx + tw / 2 - 14, cy - 6), "ms", font=unit_font, fill=MUTED)

    sub = "WebSocket Round-trip"
    draw.text((cx - _text_w(draw, sub, label_font) / 2, cy + 42), sub, font=label_font, fill=MUTED)

    if api_ms is not None:
        chip_text = f"REST API   {api_ms} ms"
        chip_w = _text_w(draw, chip_text, label_font) + 32
        chip_box = [cx - chip_w / 2, cy + r + 18, cx + chip_w / 2, cy + r + 52]
        canvas = _overlay(canvas, lambda d: d.rounded_rectangle(chip_box, radius=18, fill=(255, 255, 255, 20)))
        draw = ImageDraw.Draw(canvas)
        draw.text((chip_box[0] + 16, chip_box[1] + 7), chip_text, font=label_font, fill=WHITE)

    return _to_bytes(canvas)


# ── PING GIF: animated rotating gauge ring (Animated GIF) ───────────


def render_animated_ping_gif(ws_ms: int, api_ms: Optional[int] = None, frames: int = 12) -> io.BytesIO:
    w, h = 760, 540
    color, tier_label = _latency_tier(ws_ms)
    frame_list = []
    
    capped = max(0, min(ws_ms, 300))
    target_sweep = (capped / 300) * 300
    
    for i in range(frames):
        canvas = _base_canvas(w, h, glow_color=color)

        card_margin = 24
        canvas.alpha_composite(_glass_card((w - card_margin * 2, h - card_margin * 2), radius=38), (card_margin, card_margin))

        draw = ImageDraw.Draw(canvas)
        title_font = _font(24)
        draw.text((card_margin + 36, card_margin + 30), "NETWORK LATENCY", font=title_font, fill=WHITE)
        
        pill_font = _font(15)
        _pill(draw, (w - card_margin - 160, card_margin + 26), tier_label, pill_font, (15, 23, 42), color, pad_x=16, pad_y=7)

        cx, cy, r = w // 2, h // 2 + 10, 135
        thickness = 24
        track_box = [cx - r, cy - r, cx + r, cy + r]
        
        current_sweep = target_sweep * (0.8 + 0.2 * (i / frames))
        start_angle = 90 + int(i * (360 / frames))
        sweep_max = 300

        canvas = _overlay(canvas, lambda d: d.arc(track_box, 90, 90 + sweep_max, fill=(255, 255, 255, 30), width=thickness))
        canvas = _overlay(canvas, lambda d: d.arc(track_box, start_angle, start_angle + current_sweep, fill=(*color, 50), width=thickness + 16))
        canvas = _overlay(canvas, lambda d: d.arc(track_box, start_angle, start_angle + current_sweep, fill=(*color, 100), width=thickness + 6))

        draw = ImageDraw.Draw(canvas)
        if current_sweep > 0:
            draw.arc(track_box, start_angle, start_angle + current_sweep, fill=color, width=thickness)

        big_font = _font(64)
        unit_font = _font(20)
        label_font = _font(16)

        value_text = f"{ws_ms}"
        tw = _text_w(draw, value_text, big_font)
        draw.text((cx - tw / 2 - 14, cy - 50), value_text, font=big_font, fill=WHITE)
        draw.text((cx + tw / 2 - 14, cy - 6), "ms", font=unit_font, fill=MUTED)

        sub = "WebSocket Round-trip"
        draw.text((cx - _text_w(draw, sub, label_font) / 2, cy + 42), sub, font=label_font, fill=MUTED)

        if api_ms is not None:
            chip_text = f"REST API   {api_ms} ms"
            chip_w = _text_w(draw, chip_text, label_font) + 32
            chip_box = [cx - chip_w / 2, cy + r + 18, cx + chip_w / 2, cy + r + 52]
            canvas = _overlay(canvas, lambda d: d.rounded_rectangle(chip_box, radius=18, fill=(255, 255, 255, 20)))
            draw = ImageDraw.Draw(canvas)
            draw.text((chip_box[0] + 16, chip_box[1] + 7), chip_text, font=label_font, fill=WHITE)

        frame_list.append(canvas.convert("RGB"))

    buf = io.BytesIO()
    frame_list[0].save(
        buf,
        format="GIF",
        save_all=True,
        append_images=frame_list[1:],
        duration=100,
        loop=0,
        optimize=True
    )
    buf.seek(0)
    return buf


# ── BOTINFO: modern dashboard stat card ─────────────────────────────


def render_bot_info_card(
    name: str,
    avatar_bytes: Optional[bytes],
    stats: list[tuple[str, str, tuple[int, int, int]]],
) -> io.BytesIO:
    w, h = 980, 560
    canvas = _base_canvas(w, h, glow_color=BLURPLE)

    card_margin = 24
    canvas.alpha_composite(_glass_card((w - card_margin * 2, h - card_margin * 2), radius=38), (card_margin, card_margin))
    draw = ImageDraw.Draw(canvas)

    pad = card_margin + 36
    avatar_size = 110
    has_avatar = False

    if avatar_bytes:
        try:
            av = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((avatar_size, avatar_size))
            canvas.alpha_composite(_glow_blob((w, h), (pad + avatar_size // 2, pad + avatar_size // 2), avatar_size, BLURPLE, alpha=100))
            av_mask = Image.new("L", (avatar_size, avatar_size), 0)
            ImageDraw.Draw(av_mask).ellipse([(0, 0), (avatar_size, avatar_size)], fill=255)
            canvas.paste(av, (pad, pad), av_mask)
            has_avatar = True
            draw = ImageDraw.Draw(canvas)
            draw.ellipse([pad - 3, pad - 3, pad + avatar_size + 3, pad + avatar_size + 3], outline=(220, 224, 245), width=3)
        except Exception:
            has_avatar = False

    text_x = pad + (avatar_size + 32 if has_avatar else 0)

    name_font = _font(34)
    draw.text((text_x, pad + 4), name, font=name_font, fill=WHITE)

    status_font = _font(14)
    status_box = [text_x, pad + 52, text_x + 108, pad + 52 + status_font.size + 14]
    draw.rounded_rectangle(status_box, radius=(status_box[3] - status_box[1]) // 2, fill=GREEN)
    _dot(draw, (text_x + 15, (status_box[1] + status_box[3]) // 2), 4, (10, 40, 20))
    draw.text((text_x + 26, status_box[1] + 6), "ONLINE", font=status_font, fill=(10, 40, 20))

    divider_y = pad + avatar_size + 22
    canvas = _overlay(canvas, lambda d: d.line(
        [(card_margin + 36, divider_y), (w - card_margin - 36, divider_y)], fill=(255, 255, 255, 45), width=1,
    ))

    grid_top = pad + avatar_size + 46
    cols = 3
    gap = 20
    tile_w = (w - card_margin * 2 - 72 - gap * (cols - 1)) // cols
    tile_h = 112
    label_font = _font(14)
    value_font = _font(28)

    for i, (label, value, accent) in enumerate(stats):
        col = i % cols
        row = i // cols
        x = card_margin + 36 + col * (tile_w + gap)
        y = grid_top + row * (tile_h + gap)

        tile = Image.new("RGBA", (tile_w, tile_h), (0, 0, 0, 0))
        tmask = _rounded_mask((tile_w, tile_h), 22)
        tfill = Image.new("RGBA", (tile_w, tile_h), (255, 255, 255, 14))
        tile.paste(tfill, (0, 0), tmask)
        tdraw = ImageDraw.Draw(tile)
        tdraw.rounded_rectangle([(0, 0), (tile_w - 1, tile_h - 1)], radius=22, outline=(255, 255, 255, 38), width=1)
        _dot(tdraw, (24, tile_h - 22), 5, accent)
        tdraw.text((38, tile_h - 30), label.upper(), font=label_font, fill=MUTED)
        tdraw.text((18, 16), value, font=value_font, fill=WHITE)
        canvas.alpha_composite(tile, (x, y))

    draw = ImageDraw.Draw(canvas)
    footer_font = _font(13)
    draw.text((card_margin + 36, h - card_margin - 32), "System Operational • Real-time telemetry", font=footer_font, fill=(130, 134, 156))

    return _to_bytes(canvas)


# ── CHART: modern vertical bar chart ────────────────────────────────


def render_bar_chart(title: str, data: dict[str, int], accent_color: tuple[int, int, int] = BLURPLE) -> io.BytesIO:
    w, h = 800, 480
    canvas = _base_canvas(w, h, glow_color=accent_color)

    card_margin = 24
    canvas.alpha_composite(_glass_card((w - card_margin * 2, h - card_margin * 2), radius=36), (card_margin, card_margin))
    
    draw = ImageDraw.Draw(canvas)
    title_font = _font(22)
    draw.text((card_margin + 36, card_margin + 30), title.upper(), font=title_font, fill=WHITE)
    
    chart_x1 = card_margin + 50
    chart_y1 = card_margin + 90
    chart_x2 = w - card_margin - 50
    chart_y2 = h - card_margin - 70
    
    chart_w = chart_x2 - chart_x1
    chart_h = chart_y2 - chart_y1
    
    keys = list(data.keys())
    values = list(data.values())
    max_val = max(values) if values else 1
    
    for i in range(4):
        gy = chart_y1 + int((chart_h / 3) * i)
        canvas = _overlay(canvas, lambda d, y=gy: d.line([(chart_x1, y), (chart_x2, y)], fill=(255, 255, 255, 20), width=1))
    
    draw = ImageDraw.Draw(canvas)
    num_bars = len(keys)
    if num_bars > 0:
        total_bar_space = chart_w / num_bars
        bar_width = int(total_bar_space * 0.55)
        bar_gap = total_bar_space - bar_width
        
        label_font = _font(13)
        val_font = _font(12)
        
        for i, (k, v) in enumerate(data.items()):
            bx = chart_x1 + int(i * total_bar_space) + int(bar_gap / 2)
            bh = int((v / max_val) * (chart_h - 30))
            by = chart_y2 - bh
            
            bar_box = [bx, by, bx + bar_width, chart_y2]
            
            canvas = _overlay(canvas, lambda d, box=bar_box, col=accent_color: d.rounded_rectangle(
                [box[0]-3, box[1]-3, box[2]+3, box[3]], radius=8, fill=(*col, 40)
            ))
            
            draw = ImageDraw.Draw(canvas)
            draw.rounded_rectangle(bar_box, radius=6, fill=accent_color)
            
            val_str = str(v)
            vw = _text_w(draw, val_str, val_font)
            draw.text((bx + (bar_width - vw) // 2, by - 20), val_str, font=val_font, fill=WHITE)
            
            kw = _text_w(draw, k, label_font)
            draw.text((bx + (bar_width - kw) // 2, chart_y2 + 12), k, font=label_font, fill=MUTED)

    return _to_bytes(canvas)


# ── COLOR: quick swatch card ────────────────────────────────────────


def render_color_card(hex_color: str, rgb: tuple[int, int, int]) -> io.BytesIO:
    w, h = 640, 280
    canvas = _base_canvas(w, h, glow_color=rgb)
    canvas.alpha_composite(_glass_card((w - 48, h - 48), radius=32), (24, 24))

    swatch_size = 150
    sx, sy = 48, (h - swatch_size) // 2
    swatch_box = [sx, sy, sx + swatch_size, sy + swatch_size]

    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(swatch_box, radius=24, fill=rgb)
    canvas = _overlay(canvas, lambda d: d.rounded_rectangle(swatch_box, radius=24, outline=(255, 255, 255, 100), width=2))
    draw = ImageDraw.Draw(canvas)

    tx = sx + swatch_size + 36
    title_font = _font(30)
    label_font = _font(15)
    value_font = _font(20)
    draw.text((tx, sy + 4), hex_color.upper(), font=title_font, fill=WHITE)
    draw.text((tx, sy + 52), "HEX CODE", font=label_font, fill=MUTED)
    draw.text((tx, sy + 72), hex_color.upper(), font=value_font, fill=WHITE)
    draw.text((tx, sy + 104), "RGB VALUES", font=label_font, fill=MUTED)
    draw.text((tx, sy + 124), f"{rgb[0]}, {rgb[1]}, {rgb[2]}", font=value_font, fill=WHITE)

    return _to_bytes(canvas)
