from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "carrosseis" / "metodo-jolt-vendas-mentoria"
PHOTO = ROOT / "minhas-fotos" / "bio-silvana-rosa-desafio-sua-mentoria-em-3-dias.webp"

W, H = 1080, 1350

COLORS = {
    "cream": "#F7F1E5",
    "cream_border": "#E8DEC9",
    "teal": "#0E4D4A",
    "teal_mid": "#1A6B66",
    "tiffany": "#4EC8C4",
    "tiffany_light": "#A8E2DF",
    "gold": "#C8A24C",
    "ink": "#10302E",
    "white": "#FFFDF8",
}

FONT_DIRS = [
    Path("C:/Windows/Fonts"),
    Path.home() / "AppData/Local/Microsoft/Windows/Fonts",
]


def font_path(*names):
    for folder in FONT_DIRS:
        for name in names:
            p = folder / name
            if p.exists():
                return str(p)
    return None


SERIF = font_path("georgiab.ttf", "georgia.ttf")
SERIF_REG = font_path("georgia.ttf")
SERIF_ITALIC = font_path("georgiai.ttf", "georgia.ttf")
SANS = font_path("arial.ttf")
SANS_BOLD = font_path("arialbd.ttf", "arial.ttf")


def f(path, size):
    return ImageFont.truetype(path, size=size)


def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def gradient(top="#0E4D4A", mid="#1A6B66", bottom="#4EC8C4"):
    img = Image.new("RGB", (W, H), top)
    draw = ImageDraw.Draw(img)
    c1, c2, c3 = map(hex_to_rgb, (top, mid, bottom))
    for y in range(H):
        t = y / (H - 1)
        if t < 0.6:
            k = t / 0.6
            c = tuple(int(c1[i] * (1 - k) + c2[i] * k) for i in range(3))
        else:
            k = (t - 0.6) / 0.4
            c = tuple(int(c2[i] * (1 - k) + c3[i] * k) for i in range(3))
        draw.line([(0, y), (W, y)], fill=c)
    return img.convert("RGBA")


def solid(color):
    return Image.new("RGBA", (W, H), color)


def add_texture(img, opacity=18):
    noise = Image.effect_noise((W, H), 18).convert("L")
    overlay = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    overlay.putalpha(noise.point(lambda p: min(opacity, int(p / 255 * opacity))))
    return Image.alpha_composite(img, overlay)


def wrap(draw, text, font, max_width):
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        line = words[0]
        for word in words[1:]:
            trial = f"{line} {word}"
            if draw.textbbox((0, 0), trial, font=font)[2] <= max_width:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def text_block(draw, xy, text, font, fill, max_width, line_gap=12, anchor="la"):
    x, y = xy
    lines = wrap(draw, text, font, max_width)
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill, anchor=anchor)
        y += int(font.size * 0.92) + line_gap
    return y


def centered_text(draw, y, text, font, fill, max_width, line_gap=10):
    lines = wrap(draw, text, font, max_width)
    total = 0
    heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line or "Ag", font=font)
        h = bbox[3] - bbox[1]
        heights.append(h)
        total += h
    total += line_gap * (len(lines) - 1)
    cy = y - total / 2
    for line, h in zip(lines, heights):
        bbox = draw.textbbox((0, 0), line, font=font)
        draw.text(((W - (bbox[2] - bbox[0])) / 2, cy), line, font=font, fill=fill)
        cy += h + line_gap


def pill(draw, xy, text, fill, text_fill, outline=None):
    x, y = xy
    font = f(SANS_BOLD, 28)
    bbox = draw.textbbox((0, 0), text, font=font)
    pad_x, pad_y = 30, 16
    rect = [x, y, x + bbox[2] + pad_x * 2, y + bbox[3] + pad_y * 2]
    draw.rounded_rectangle(rect, radius=36, fill=fill, outline=outline, width=2)
    draw.text((x + pad_x, y + pad_y - 2), text, font=font, fill=text_fill)


def footer(draw, number, total, dark=False):
    color = COLORS["cream"] if dark else COLORS["ink"]
    muted = COLORS["tiffany_light"] if dark else COLORS["teal_mid"]
    draw.line((90, 1232, 945, 1232), fill=muted, width=2)
    draw.text((90, 1265), "@eu.silvanarosa", font=f(SANS_BOLD, 27), fill=color)
    draw.text((945, 1265), f"{number:02d}/{total:02d}", font=f(SERIF_REG, 32), fill=color, anchor="ra")


def photo_card(img, box, radius=46):
    src = Image.open(PHOTO).convert("RGBA")
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    src_ratio = src.width / src.height
    box_ratio = bw / bh
    if src_ratio > box_ratio:
        nh = bh
        nw = int(nh * src_ratio)
    else:
        nw = bw
        nh = int(nw / src_ratio)
    src = src.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - bw) // 2
    top = max(0, (nh - bh) // 2 - 30)
    src = src.crop((left, top, left + bw, top + bh))

    mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, bw, bh), radius=radius, fill=255)
    shadow = Image.new("RGBA", (bw + 50, bh + 50), (0, 0, 0, 0))
    shadow_mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(shadow_mask).rounded_rectangle((0, 0, bw, bh), radius=radius, fill=120)
    shadow.paste((0, 0, 0, 120), (25, 25), shadow_mask)
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    img.alpha_composite(shadow, (x1 - 25, y1 - 20))
    img.paste(src, (x1, y1), mask)
    return img


def decorative(draw, dark=False):
    accent = COLORS["gold"] if dark else COLORS["tiffany"]
    for i in range(3):
        r = 110 + i * 60
        box = (W - 180 - r, 70 - r, W - 180 + r, 70 + r)
        draw.arc(box, 18, 145, fill=accent, width=2)
    draw.ellipse((78, 94, 91, 107), fill=accent)
    draw.ellipse((960, 1115, 975, 1130), fill=accent)


slides = [
    {
        "kind": "cover",
        "bg": "dark",
        "tag": "METODO JOLT",
        "title": "Seu cliente diz:\n“vou pensar”?",
        "subtitle": "Talvez ele não precise de mais valor. Ele precisa de segurança para decidir.",
    },
    {
        "bg": "light",
        "tag": "O PROBLEMA",
        "title": "Ele reconhece seu valor.\nMas nao compra.",
        "subtitle": "Na venda de mentoria, o obstáculo muitas vezes não é preço, nem falta de desejo. É indecisão.",
    },
    {
        "bg": "dark",
        "tag": "A RAIZ",
        "title": "Não é falta de valor.\nÉ medo de errar.",
        "subtitle": "O lead teme escolher errado, não conseguir aplicar ou se frustrar de novo.",
    },
    {
        "bg": "light",
        "tag": "J DE JULGAR",
        "title": "Entenda o tipo\nde medo.",
        "bullets": ["Medo de escolher errado", "Falta de clareza", "Dúvida se vai implementar"],
    },
    {
        "bg": "dark",
        "tag": "SINAIS",
        "title": "Como a indecisão\naparece na conversa",
        "bullets": ["Pede mais dados sem avançar", "Lembra experiências ruins", "Some, distrai ou diz qualquer coisa"],
    },
    {
        "bg": "light",
        "tag": "O DE OFERECER",
        "title": "Recomende o melhor caminho.",
        "subtitle": "Cliente indeciso não precisa de dez opções. Precisa que você conduza com autoridade.",
        "quote": "“Para o seu objetivo, este é o caminho mais direto.”",
    },
    {
        "bg": "dark",
        "tag": "L DE LIMITAR",
        "title": "Pare de aumentar\na confusao.",
        "subtitle": "Mais PDF, mais reunião e mais comparação podem travar ainda mais a decisão.",
        "quote": "“Já temos as informações necessárias para decidir.”",
    },
    {
        "bg": "light",
        "tag": "T DE TIRAR O RISCO",
        "title": "Reduza o medo\ndo fracasso.",
        "bullets": ["Garantia de implementação", "Diagnóstico inicial", "Expectativas claras"],
    },
    {
        "bg": "dark",
        "tag": "APLICAÇÃO",
        "title": "JOLT transforma\nhesitação em ação.",
        "subtitle": "Você guia o cliente para sair da análise infinita e entrar em movimento.",
    },
    {
        "kind": "cta",
        "bg": "gradient",
        "tag": "PROXIMO PASSO",
        "title": "Quer destravar\nsuas vendas?",
        "subtitle": "Me chama no direct com a palavra JOLT e vamos olhar o que está travando suas mentorias.",
    },
]


def draw_slide(data, idx, total):
    dark = data["bg"] in ("dark", "gradient")
    if data["bg"] == "gradient":
        img = gradient()
    else:
        img = solid(COLORS["teal"] if dark else COLORS["cream"])
    img = add_texture(img, 12 if dark else 18)
    draw = ImageDraw.Draw(img)
    decorative(draw, dark=dark)

    title_color = COLORS["cream"] if dark else COLORS["ink"]
    body_color = COLORS["white"] if dark else COLORS["ink"]
    tag_fill = COLORS["tiffany"] if dark else COLORS["teal"]
    tag_text = COLORS["teal"] if dark else COLORS["cream"]

    pill(draw, (90, 92), data["tag"], tag_fill, tag_text)

    if data.get("kind") == "cover":
        photo_card(img, (612, 192, 980, 705), radius=170)
        draw.text((90, 282), "Metodo", font=f(SANS_BOLD, 28), fill=COLORS["tiffany_light"])
        draw.text((90, 325), "JOLT", font=f(SERIF, 148), fill=COLORS["gold"])
        text_block(draw, (90, 520), data["title"], f(SERIF, 68), title_color, 630, line_gap=18)
        text_block(draw, (90, 760), data["subtitle"], f(SANS, 36), body_color, 760, line_gap=14)
    elif data.get("kind") == "cta":
        photo_card(img, (640, 180, 980, 640), radius=160)
        text_block(draw, (90, 315), data["title"], f(SERIF, 88), title_color, 620, line_gap=12)
        text_block(draw, (90, 615), data["subtitle"], f(SANS, 38), body_color, 820, line_gap=15)
        draw.rounded_rectangle((90, 900, 810, 1018), radius=58, fill=COLORS["cream"])
        draw.text((135, 936), "mande JOLT no direct", font=f(SANS_BOLD, 40), fill=COLORS["teal"])
    else:
        text_block(draw, (90, 260), data["title"], f(SERIF, 74), title_color, 850, line_gap=12)
        y = 565
        if "subtitle" in data:
            y = text_block(draw, (90, y), data["subtitle"], f(SANS, 38), body_color, 810, line_gap=16)
            y += 45
        if "bullets" in data:
            y = 585
            for b in data["bullets"]:
                draw.rounded_rectangle((90, y - 12, 145, y + 43), radius=27, fill=COLORS["tiffany"])
                draw.text((118, y + 15), "✓", font=f(SANS_BOLD, 30), fill=COLORS["teal"], anchor="mm")
                text_block(draw, (170, y - 6), b, f(SANS_BOLD, 38), body_color, 760, line_gap=10)
                y += 135
        if "quote" in data:
            draw.rounded_rectangle((90, y, 945, y + 210), radius=38, fill=COLORS["cream"] if dark else COLORS["teal"], outline=COLORS["gold"], width=3)
            q_fill = COLORS["teal"] if dark else COLORS["cream"]
            text_block(draw, (135, y + 55), data["quote"], f(SERIF_ITALIC, 42), q_fill, 760, line_gap=10)

    footer(draw, idx, total, dark=dark)
    return img.convert("RGB")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    total = len(slides)
    for i, data in enumerate(slides, 1):
        img = draw_slide(data, i, total)
        img.save(OUT / f"slide-{i:02d}.png", "PNG")

    sheet = Image.new("RGB", (5 * 216, 2 * 270), COLORS["cream"])
    for i in range(total):
        thumb = Image.open(OUT / f"slide-{i + 1:02d}.png").resize((216, 270), Image.Resampling.LANCZOS)
        sheet.paste(thumb, ((i % 5) * 216, (i // 5) * 270))
    sheet.save(OUT / "contact-sheet.png", "PNG")
    print(f"Generated {total} slides in {OUT}")


if __name__ == "__main__":
    main()
