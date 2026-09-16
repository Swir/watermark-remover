from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "watermark-remover.ico"

def draw(size: int = 512) -> Image.Image:
    img = Image.new("RGBA", (size, size), (5, 8, 22, 255)); glow = Image.new("RGBA", img.size, (0,0,0,0)); gd = ImageDraw.Draw(glow)
    gd.rounded_rectangle((40,40,size-40,size-40), radius=94, outline=(76,201,255,190), width=22); img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(16)))
    d = ImageDraw.Draw(img); d.rounded_rectangle((40,40,size-40,size-40), radius=94, outline=(67,97,238,255), width=14)
    d.rounded_rectangle((92,132,420,368), radius=42, fill=(9,27,53,255), outline=(76,201,255,255), width=12)
    d.ellipse((128,178,232,282), outline=(225,248,255,255), width=16); d.line((158,257,214,201), fill=(225,248,255,255), width=16)
    d.polygon([(278,184),(366,272),(277,361),(199,368),(207,291)], fill=(7,16,31,255), outline=(76,201,255,255)); d.line((208,292,277,361), fill=(225,248,255,255), width=13); d.line((292,202,363,273), fill=(225,248,255,255), width=13); d.line((130,412,382,412), fill=(94,230,168,255), width=10)
    return img

if __name__ == "__main__":
    image = draw(); image.save(OUT, format="ICO", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)]); print(OUT)
