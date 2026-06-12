from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
import random


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "carrosseis" / "metodo-jolt-vendas-mentoria"
PHOTO = ROOT / "minhas-fotos" / "bio-silvana-rosa-desafio-sua-mentoria-em-3-dias.webp"

W, H = 1080, 1350
TOTAL = 7

COLORS = {
    "cream": "#F7F1E5",
    "cream_2": "#FFF8EA",
    "teal": "#062F31",
    "teal_2": "#0E4D4A",
    "teal_3": "#145E59",
    "tiffany": "#4EC8C4",
    "tiffany_light": "#A8E2DF",
    "gold": "#C8A24C",
    "gold_light": "#F3D992",
    "ink": "#10302E",
    "white": "#FFFDF8",
}

FONT_DIRS = [
    Path("C:/Windows/Fonts"),
    Path.home() / "AppData/Local/Microsoft/Windows/Fonts",
]


def find_font(*names):
    for folder in FONT_DIRS:
        for name in names:
            p = folder / name
            if p.exists():
                return str(p)
    return None


SERIF = find_font("georgiab.ttf", "georgia.ttf")
SERIF_REG = find_font("georgia.ttf")
SERIF_ITALIC = find_font("georgiai.ttf", "georgia.ttf")
SANS = find_font("arial.ttf")
SANS_BOLD = find_font("arialbd.ttf", "arial.ttf")


def font(path, size):
    return ImageFont.truetype(path, size=size)


def rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lerp(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def dark_canvas():
    top, mid, bottom = rgb("#021C1E"), rgb(COLORS["teal"]), rgb("#0B615C")
    img = Image.new("RGB", (W, H), top)
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        c = lerp(top, mid, t / 0.72) if t < 0.72 else lerp(mid, bottom, (t - 0.72) / 0.28)
        draw.line((0, y, W, y), fill=c)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((590, -160, 1260, 520), fill=(223, 177, 87, 72))
    gd.ellipse((-260, 820, 620, 1530), fill=(78, 200, 196, 48))
    glow = glow.filter(ImageFilter.GaussianBlur(70))
    return Image.alpha_composite(img.convert("RGBA"), glow)


def light_canvas():
    img = Image.new("RGBA", (W, H), COLORS["cream"])
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-260, 980, 620, 1540), fill=(78, 200, 196, 78))
    gd.ellipse((740, -250, 1320, 330), fill=(243, 217, 146, 42))
    glow = glow.filter(ImageFilter.GaussianBlur(80))
    img = Image.alpha_composite(img, glow)
    return img


def add_noise(img, opacity=14):
    noise = Image.effect_noise((W, H), 20).convert("L")
    layer = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    layer.putalpha(noise.point(lambda p: int(p / 255 * opacity)))
    return Image.alpha_composite(img, layer)


def title_shadow(draw, pos, text, fnt, fill, shadow=(0, 0, 0, 95), anchor=None, stroke=0):
    x, y = pos
    draw.text((x + 3, y + 5), text, font=fnt, fill=shadow, anchor=anchor, stroke_width=stroke, stroke_fill=shadow)
    draw.text((x, y), text, font=fnt, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=fill)


def measure(draw, text, fnt):
    b = draw.textbbox((0, 0), text, font=fnt)
    return b[2] - b[0], b[3] - b[1]


def wrap(draw, text, fnt, max_w):
    lines = []
    for para in text.split("\n"):
        words = para.split()
        if not words:
            lines.append("")
            continue
        line = words[0]
        for word in words[1:]:
            test = f"{line} {word}"
            if measure(draw, test, fnt)[0] <= max_w:
                line = test
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def draw_wrapped(draw, xy, text, fnt, fill, max_w, gap=12, shadow=False, align="left"):
    x, y = xy
    for line in wrap(draw, text, fnt, max_w):
        w, _ = measure(draw, line, fnt)
        tx = x if align == "left" else x + (max_w - w) / 2
        if shadow:
            title_shadow(draw, (tx, y), line, fnt, fill)
        else:
            draw.text((tx, y), line, font=fnt, fill=fill)
        y += int(fnt.size * 1.02) + gap
    return y


def crop_photo(size, focus_y=-40):
    src = Image.open(PHOTO).convert("RGBA")
    sw, sh = src.size
    bw, bh = size
    scale = max(bw / sw, bh / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    src = src.resize((nw, nh), Image.Resampling.LANCZOS)
    left = max(0, (nw - bw) // 2)
    top = min(max(0, (nh - bh) // 2 + focus_y), max(0, nh - bh))
    return src.crop((left, top, left + bw, top + bh))


def add_photo_right(img, x=560, y=118, w=555, h=1050, opacity=245):
    photo = crop_photo((w, h), -70)
    photo = photo.filter(ImageFilter.UnsharpMask(radius=1.2, percent=112, threshold=4))
    mask = Image.new("L", (w, h), 255)
    fade = Image.new("L", (w, h), 0)
    fd = ImageDraw.Draw(fade)
    fd.rectangle((0, 0, w, h), fill=255)
    for i in range(130):
        fd.line((i, 0, i, h), fill=int(255 * i / 130))
    for i in range(120):
        fd.line((0, h - i, w, h - i), fill=int(255 * i / 120))
    mask = ImageChops_multiply(mask, fade).point(lambda p: min(p, opacity))
    img.paste(photo, (x, y), mask)
    return img


def ImageChops_multiply(a, b):
    from PIL import ImageChops
    return ImageChops.multiply(a, b)


def waves(draw, dark=True):
    base = rgb(COLORS["tiffany"] if dark else COLORS["tiffany"])
    gold = rgb(COLORS["gold"])
    for i in range(17):
        pts = []
        for x in range(-80, W + 90, 12):
            y = 1130 + i * 8 + math.sin((x / 96) + i * 0.35) * 34
            pts.append((x, y))
        color = base if i % 2 else gold
        alpha = 82 if dark else 54
        draw.line(pts, fill=color + (alpha,), width=1)


def star(draw, x, y, r=18, fill=None):
    fill = fill or COLORS["gold"]
    pts = [(x, y - r), (x + r * .22, y - r * .22), (x + r, y), (x + r * .22, y + r * .22),
           (x, y + r), (x - r * .22, y + r * .22), (x - r, y), (x - r * .22, y - r * .22)]
    draw.polygon(pts, fill=fill)


def fine_ornaments(draw, dark=True):
    gold = COLORS["gold_light"] if dark else COLORS["gold"]
    tiff = COLORS["tiffany"]
    for r in range(120, 310, 32):
        draw.arc((790 - r, 65 - r, 790 + r, 65 + r), 20, 128, fill=gold, width=1)
    for i in range(8):
        draw.ellipse((78, 100 + i * 24, 84, 106 + i * 24), fill=gold)
    star(draw, 940, 238, 23, tiff)
    star(draw, 280, 1185, 15, gold)


def line_network(draw, points):
    for a, b in zip(points, points[1:]):
        draw.line((a, b), fill=rgb(COLORS["gold"]) + (150,), width=2)
    for x, y in points:
        draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=COLORS["gold_light"])
        draw.ellipse((x - 14, y - 14, x + 14, y + 14), outline=rgb(COLORS["gold"]) + (80,), width=2)


def icon(draw, cx, cy, kind, scale=1.0, color=None):
    c = color or COLORS["tiffany"]
    gold = COLORS["gold_light"]
    sw = max(3, int(5 * scale))
    if kind == "person":
        draw.ellipse((cx - 24*scale, cy - 48*scale, cx + 24*scale, cy), outline=c, width=sw)
        draw.rounded_rectangle((cx - 48*scale, cy + 10*scale, cx + 48*scale, cy + 70*scale), radius=int(22*scale), outline=c, width=sw)
        star(draw, cx + 48*scale, cy - 32*scale, int(12*scale), gold)
    elif kind == "shield":
        pts = [(cx, cy - 56*scale), (cx + 50*scale, cy - 30*scale), (cx + 38*scale, cy + 42*scale),
               (cx, cy + 72*scale), (cx - 38*scale, cy + 42*scale), (cx - 50*scale, cy - 30*scale)]
        draw.line(pts + [pts[0]], fill=c, width=sw)
        star(draw, cx, cy + 2*scale, int(18*scale), gold)
    elif kind == "chat":
        draw.rounded_rectangle((cx - 58*scale, cy - 44*scale, cx + 58*scale, cy + 35*scale), radius=int(28*scale), outline=c, width=sw)
        draw.line((cx - 18*scale, cy + 35*scale, cx - 42*scale, cy + 58*scale), fill=c, width=sw)
        for dx in (-26, 0, 26):
            draw.ellipse((cx + dx*scale - 7, cy - 8*scale, cx + dx*scale + 7, cy + 6*scale), fill=gold)
    elif kind == "chart":
        for i, h in enumerate([28, 48, 76]):
            x = cx - 52*scale + i * 42*scale
            draw.rounded_rectangle((x, cy + 54*scale - h*scale, x + 20*scale, cy + 54*scale), radius=5, fill=c if i != 1 else gold)
        draw.line((cx - 58*scale, cy + 58*scale, cx + 56*scale, cy + 58*scale), fill=c, width=sw)
        draw.line((cx - 44*scale, cy - 5*scale, cx - 8*scale, cy - 30*scale, cx + 42*scale, cy - 70*scale), fill=c, width=sw)
    elif kind == "compass":
        draw.ellipse((cx - 58*scale, cy - 58*scale, cx + 58*scale, cy + 58*scale), outline=c, width=sw)
        draw.polygon([(cx, cy - 42*scale), (cx + 16*scale, cy + 8*scale), (cx, cy), (cx - 16*scale, cy + 8*scale)], fill=gold)
    elif kind == "lock":
        draw.arc((cx - 36*scale, cy - 60*scale, cx + 36*scale, cy + 22*scale), 180, 360, fill=c, width=sw)
        draw.rounded_rectangle((cx - 58*scale, cy - 8*scale, cx + 58*scale, cy + 72*scale), radius=int(18*scale), outline=c, width=sw)
        star(draw, cx, cy + 32*scale, int(14*scale), gold)


def glass_card(draw, x, y, w, h, kind="chat", label=None, dark=True):
    fill = (4, 48, 49, 105) if dark else (255, 253, 248, 150)
    outline = rgb(COLORS["gold"]) + (150,)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=28, fill=fill, outline=outline, width=2)
    icon(draw, x + w/2, y + h/2 - 18, kind, .72, COLORS["tiffany"])
    if label:
        draw.line((x + 44, y + h - 48, x + w - 44, y + h - 48), fill=rgb(COLORS["gold"]) + (90,), width=2)
        draw.text((x + w/2, y + h - 35), label, font=font(SANS_BOLD, 18), fill=COLORS["cream"] if dark else COLORS["ink"], anchor="ma")


def footer(draw, n, dark=True):
    y = 1240
    color = COLORS["cream"] if dark else COLORS["ink"]
    gold = COLORS["gold"]
    draw.line((180, y, 435, y), fill=gold, width=2)
    draw.line((650, y, 900, y), fill=gold, width=2)
    star(draw, 435, y, 10, COLORS["gold_light"])
    star(draw, 650, y, 10, COLORS["gold_light"])
    draw.text((540, 1202), str(n), font=font(SERIF_REG, 76), fill=gold, anchor="ra")
    draw.text((548, 1228), f"/{TOTAL}", font=font(SERIF_REG, 38), fill=color, anchor="la")


def pill(draw, x, y, text, light=False):
    fnt = font(SANS_BOLD, 24)
    tw, th = measure(draw, text, fnt)
    fill = COLORS["teal_2"] if light else COLORS["tiffany"]
    fg = COLORS["cream"] if light else COLORS["teal"]
    draw.rounded_rectangle((x, y, x + tw + 42, y + 44), radius=22, fill=fill)
    draw.text((x + 21, y + 10), text, font=fnt, fill=fg)


def dark_slide(n, title_lines, subtitle=None, photo=False, cards=None, cta=False, network=None):
    img = add_noise(dark_canvas(), 11)
    draw = ImageDraw.Draw(img, "RGBA")
    waves(draw, True)
    fine_ornaments(draw, True)
    if photo:
        add_photo_right(img, 545 if cta else 560, 80 if cta else 110, 575, 1120)
        draw = ImageDraw.Draw(img, "RGBA")
    if cards:
        line_network(draw, network or [(590, 230), (720, 370), (655, 555), (792, 720), (685, 905)])
        for c in cards:
            glass_card(draw, *c)
    return img, draw


def light_slide():
    img = add_noise(light_canvas(), 16)
    draw = ImageDraw.Draw(img, "RGBA")
    fine_ornaments(draw, False)
    waves(draw, False)
    return img, draw


def card_module(draw, x, y, w, h, num, head, body, kind):
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((x + 10, y + 15, x + w + 10, y + h + 15), radius=28, fill=(5, 49, 50, 65))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    draw.bitmap((0, 0), shadow.split()[-1], fill=(5, 49, 50, 40))
    draw.rounded_rectangle((x, y, x + w, y + h), radius=28, fill=COLORS["teal_2"], outline=COLORS["gold"], width=3)
    draw.ellipse((x + w/2 - 58, y + 40, x + w/2 + 58, y + 156), outline=COLORS["gold_light"], width=3)
    icon(draw, x + w/2, y + 95, kind, .55, COLORS["tiffany"])
    draw.text((x + w/2, y + 182), f"{num:02d}", font=font(SERIF_REG, 50), fill=COLORS["tiffany"], anchor="ma")
    draw_wrapped(draw, (x + 32, y + 246), head, font(SERIF, 29), COLORS["cream"], w - 64, 4, align="center")
    star(draw, x + w/2, y + 344, 13, COLORS["gold_light"])
    draw.line((x + 72, y + 344, x + w/2 - 22, y + 344), fill=COLORS["gold_light"], width=2)
    draw.line((x + w/2 + 22, y + 344, x + w - 72, y + 344), fill=COLORS["gold_light"], width=2)
    draw_wrapped(draw, (x + 42, y + 384), body, font(SANS, 28), COLORS["white"], w - 84, 7, align="center")


def split_card(draw, x, y, w, h, title, body, kind):
    draw.rounded_rectangle((x, y, x + w, y + h), radius=24, fill=(255, 253, 248, 210), outline=COLORS["gold"], width=2)
    draw.rounded_rectangle((x, y + h * .56, x + w, y + h), radius=24, fill=COLORS["teal_2"])
    draw.rectangle((x, y + h * .56, x + w, y + h * .65), fill=COLORS["teal_2"])
    draw.ellipse((x + w/2 - 58, y - 48, x + w/2 + 58, y + 68), fill=COLORS["teal_2"], outline=COLORS["gold"], width=3)
    icon(draw, x + w/2, y + 14, kind, .45, COLORS["tiffany"])
    draw_wrapped(draw, (x + 28, y + 90), title, font(SERIF, 31), COLORS["ink"], w - 56, 4, align="center")
    star(draw, x + w/2, y + h * .56, 14, COLORS["gold"])
    draw_wrapped(draw, (x + 34, y + h * .64), body, font(SANS, 27), COLORS["cream"], w - 68, 7, align="center")


def make_slide_1():
    img, draw = dark_slide(
        1,
        None,
        photo=True,
        cards=[(875, 150, 150, 150, "shield", None), (800, 800, 175, 150, "lock", None)],
        network=[(590, 230), (720, 365), (835, 555), (760, 730), (690, 900)],
        cta=False,
    )
    pill(draw, 84, 92, "METODO JOLT")
    title_shadow(draw, (82, 305), "MENTORA:", font(SERIF_REG, 70), COLORS["gold_light"])
    title_shadow(draw, (82, 390), "SEU CLIENTE", font(SERIF, 86), COLORS["cream"])
    title_shadow(draw, (82, 500), "DISSE", font(SERIF, 86), COLORS["cream"])
    title_shadow(draw, (82, 612), "“VOU PENSAR”?", font(SERIF, 70), COLORS["gold_light"])
    draw.line((84, 720, 450, 720), fill=COLORS["gold"], width=3)
    draw_wrapped(draw, (84, 765), "Talvez ele não precise de mais argumento. Ele precisa de segurança para decidir.", font(SANS, 38), COLORS["cream"], 500, 12)
    footer(draw, 1, True)
    return img


def make_slide_2():
    img, draw = dark_slide(2, None, photo=False, cards=[(655, 130, 190, 190, "person", None), (785, 415, 170, 170, "shield", None), (600, 700, 210, 170, "chat", None), (770, 900, 185, 150, "chart", None)])
    title_shadow(draw, (82, 300), "NÃO É", font(SERIF_REG, 86), COLORS["gold_light"])
    title_shadow(draw, (82, 405), "FALTA DE", font(SERIF, 92), COLORS["cream"])
    title_shadow(draw, (82, 515), "VALOR", font(SERIF, 96), COLORS["cream"])
    draw.line((84, 640, 492, 640), fill=COLORS["gold"], width=3)
    draw_wrapped(draw, (84, 700), "É medo de escolher errado, aplicar errado ou se frustrar de novo.", font(SANS, 42), COLORS["cream"], 520, 14)
    footer(draw, 2, True)
    return img


def make_slide_3():
    img, draw = light_slide()
    draw_wrapped(draw, (92, 112), "JULGUE A\nINDECISÃO", font(SERIF, 82), COLORS["ink"], 900, 8, align="center")
    draw.line((302, 326, 778, 326), fill=COLORS["gold"], width=2)
    star(draw, 540, 326, 17, COLORS["gold"])
    draw.text((540, 380), "Antes de responder, descubra qual medo está travando a compra.", font=font(SANS, 34), fill=COLORS["ink"], anchor="ma")
    card_module(draw, 70, 520, 285, 560, 1, "Medo de\nescolher errado", "Ele quer certeza antes de se comprometer.", "compass")
    card_module(draw, 397, 520, 285, 560, 2, "Falta de\nclareza", "Pede mais dados, mesmo depois da explicação.", "chat")
    card_module(draw, 724, 520, 285, 560, 3, "Medo de\nnão aplicar", "A dúvida é: será que eu consigo?", "person")
    footer(draw, 3, False)
    return img


def make_slide_4():
    img, draw = light_slide()
    draw_wrapped(draw, (90, 115), "OFEREÇA\nRECOMENDAÇÃO", font(SERIF, 76), COLORS["ink"], 900, 8, align="center")
    draw.text((540, 340), "Clientes indecisos não precisam de dez opções.", font=font(SANS, 35), fill=COLORS["ink"], anchor="ma")
    draw.text((540, 392), "Precisam de direção.", font=font(SANS_BOLD, 39), fill=COLORS["teal_2"], anchor="ma")
    split_card(draw, 120, 555, 840, 345, "A frase que muda o ritmo da venda", "“Com base no seu objetivo, este é o caminho mais direto para você.”", "compass")
    draw.rounded_rectangle((175, 965, 905, 1065), radius=46, fill=COLORS["teal_2"], outline=COLORS["gold"], width=2)
    draw.text((540, 997), "assuma a condução com autoridade", font=font(SANS_BOLD, 32), fill=COLORS["cream"], anchor="ma")
    footer(draw, 4, False)
    return img


def make_slide_5():
    img, draw = light_slide()
    draw_wrapped(draw, (88, 105), "LIMITE A\nEXPLORAÇÃO", font(SERIF, 82), COLORS["ink"], 900, 8, align="center")
    draw.text((540, 356), "Mais informação pode virar mais paralisia.", font=font(SANS, 36), fill=COLORS["ink"], anchor="ma")
    split_card(draw, 95, 505, 420, 285, "Pare de empilhar materiais", "PDF, call extra e novas opções podem confundir ainda mais.", "chat")
    split_card(draw, 565, 505, 420, 285, "Feche o campo de decisão", "Volte para a solução que você recomendou.", "shield")
    split_card(draw, 212, 860, 655, 245, "Assuma o controle da conversa", "“Já temos as informações necessárias para decidir.”", "lock")
    footer(draw, 5, False)
    return img


def make_slide_6():
    img, draw = light_slide()
    draw_wrapped(draw, (88, 100), "TIRE O RISCO\nDA MESA", font(SERIF, 82), COLORS["ink"], 900, 8, align="center")
    draw.text((540, 352), "A decisão fica mais leve quando o medo perde força.", font=font(SANS, 34), fill=COLORS["ink"], anchor="ma")
    card_module(draw, 70, 510, 285, 560, 1, "Garantia de\nimplementação", "Apoio claro para quem executa de verdade.", "shield")
    card_module(draw, 397, 510, 285, 560, 2, "Comece\nmenor", "Um diagnóstico inicial reduz a pressão.", "compass")
    card_module(draw, 724, 510, 285, 560, 3, "Franqueza\nradical", "Mostre o que esperar e o que não esperar.", "chat")
    footer(draw, 6, False)
    return img


def make_slide_7():
    img, draw = dark_slide(
        7,
        None,
        photo=True,
        cards=[(850, 145, 150, 150, "person", None), (690, 805, 190, 160, "chart", None)],
        network=[(590, 230), (720, 365), (655, 555), (792, 720), (685, 905)],
        cta=True,
    )
    title_shadow(draw, (75, 270), "DESTRAVE", font(SERIF, 92), COLORS["gold_light"])
    title_shadow(draw, (75, 385), "SUAS", font(SERIF, 92), COLORS["cream"])
    title_shadow(draw, (75, 500), "VENDAS", font(SERIF, 92), COLORS["cream"])
    draw.line((78, 620, 480, 620), fill=COLORS["gold"], width=3)
    draw_wrapped(draw, (78, 675), "Quer 1h comigo para enxergar onde sua venda de mentoria está travando?", font(SANS, 39), COLORS["cream"], 500, 12)
    draw.rounded_rectangle((78, 900, 640, 1016), radius=56, fill=COLORS["cream"], outline=COLORS["gold_light"], width=3)
    draw.text((358, 936), "Comenta JOLT", font=font(SANS_BOLD, 42), fill=COLORS["ink"], anchor="ma")
    footer(draw, 7, True)
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    makers = [make_slide_1, make_slide_2, make_slide_3, make_slide_4, make_slide_5, make_slide_6, make_slide_7]
    for i, make in enumerate(makers, 1):
        img = make().convert("RGB")
        img.save(OUT / f"slide-{i:02d}.png", "PNG")
    for old in range(len(makers) + 1, 11):
        p = OUT / f"slide-{old:02d}.png"
        if p.exists():
            p.unlink()
    sheet = Image.new("RGB", (4 * 216, 2 * 270), COLORS["cream"])
    for i in range(len(makers)):
        thumb = Image.open(OUT / f"slide-{i + 1:02d}.png").resize((216, 270), Image.Resampling.LANCZOS)
        sheet.paste(thumb, ((i % 4) * 216, (i // 4) * 270))
    sheet.save(OUT / "contact-sheet.png", "PNG")
    print(f"Generated {len(makers)} slides in {OUT}")


if __name__ == "__main__":
    main()
