"""Lembar seluruh jenis benda renderer dalam dua keadaan tanpa MP4/TTS/LLM."""
from __future__ import annotations

import io
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

AKAR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AKAR / "mesin-video"))
sys.path.insert(0, str(AKAR))
UKURAN = AKAR / "newmotion" / "application" / "data" / "ukuran_benda.json"
DURASI = 3.0
LEBAR, TINGGI = 1080, 1920
POTONG = (140, 900, 940, 1700)
KOLUM, LEBAR_KOTAK, TINGGI_KOTAK = 4, 360, 196
UKURAN_PANEL = (156, 156)

# Pilih keadaan yang paling menjelaskan perubahan tiap benda jika memiliki banyak parameter.
PRIORITAS = {
    "ngarai": "lubang", "arus": "maju", "ombak": "tinggi", "bahtera": "jadi",
    "hewan": "jalan", "surya": "r", "genangan_tubuh": "tinggi",
    "resapan_tanah": "kedalaman", "naungan_kelompok": "luas",
    "gedung": "tumbuh", "kerumunan": "api", "cawan": "didih",
    "rantai_tarik": "tarik", "massa_api": "kuat", "lahar": "kuat",
    "mobil_luar": "jalan", "retakan": "buka", "bayang_misteri": "besar",
    "belah": "buka", "jurang": "jatuh", "zaqqum": "tumbuh",
    "sungai": "arus", "perahu_kecil": "goyang", "kapal_dagang": "muatan",
    "awan_badai": "hujan", "keranjang": "penuh",
}

PROPERTI_UJI = {
    "arus": {"n": 18}, "kerumunan": {"n": 24, "w": 420},
    "saf": {"n": 18, "baris": 3}, "buku": {"teks": "Contoh uji", "sub": "PRATINJAU"},
    "kartu_dalil": {"kitab": "CONTOH UJI", "no": "—", "teks": "Pratinjau visual", "label": "CONTOH"},
    "chat": {"nama": "Contoh", "pesan": [[0, "Uji renderer", "12:00", True]]},
    "monitor": {"judul": "Pratinjau", "nama": "Renderer", "teks": "Uji visual"},
    "ponsel": {"judul": "Uji renderer", "teks": "Pratinjau visual"},
    "rincian": {"judul": "Ringkasan uji", "gaji": 1000000, "baris": [[0, "Contoh", 1]], "akhir": "Selesai"},
    "logo_app": {"teks": "UJI"}, "stempel": {"teks": "UJI"},
    "tanda": {"ok": True}, "kalender": {"bulan": "Januari", "tgl": 15, "mulai": 0},
    "nur": {"nama": "Nur", "nama_s": "Nur"}, "bintang": {"n": 8},
    "makam": {"n": 3}, "dompet": {"isi": 2}, "koin": {"n": 4},
    "uang": {"n": 4},
}


def rentang(nama: str, parameter: str) -> tuple[float, float]:
    """Rentang visual yang aman; override per benda untuk parameter bersatuan khusus."""
    khusus = {
        ("genangan_tubuh", "tinggi"): (35, 440),
        ("resapan_tanah", "kedalaman"): (0.15, 1.0),
        ("naungan_kelompok", "luas"): (0.2, 1.0),
        ("timbangan", "miring"): (-18, 18),
        ("ombak", "tinggi"): (80, 500),
        ("surya", "r"): (140, 620),
        ("massa_api", "r"): (180, 780),
        ("gelap", "r"): (0, 3000),
        ("rantai_tarik", "tarik"): (0, 420),
        ("setir", "putar"): (-30, 30),
        ("bahtera", "goyang"): (-8, 8),
        ("mobil_luar", "jalan"): (0, 120),
        ("pancar", "tinggi"): (80, 600),
    }
    if (nama, parameter) in khusus:
        return khusus[(nama, parameter)]
    if parameter == "tinggi":
        return (80, 500)
    if parameter == "r":
        return (120, 620)
    if parameter == "putar":
        return (-30, 30)
    if parameter == "tarik":
        return (0, 420)
    if parameter == "besar":
        return (0.35, 1.0)
    if parameter == "kedalaman":
        return (0.15, 1.0)
    return (0.0, 1.0)


def keadaan(nama: str, info: dict) -> tuple[dict, str | None, list[float] | None]:
    animasi = info.get("animasi") or []
    if not animasi:
        return {}, None, None
    pilihan = PRIORITAS.get(nama)
    if pilihan not in animasi:
        pilihan = animasi[0]
    awal, akhir = rentang(nama, pilihan)
    return {pilihan: [awal, akhir]}, pilihan, [awal, akhir]


def penempatan(kotak: list[float] | None) -> tuple[float, float, float]:
    if not kotak or len(kotak) != 4:
        return 540, 1300, 0.7
    kiri, atas, kanan, bawah = map(float, kotak)
    lebar, tinggi = max(1.0, kanan - kiri), max(1.0, bawah - atas)
    skala = min(1.25, 620 / max(lebar, tinggi))
    tengah_x, tengah_y = (kiri + kanan) / 2, (atas + bawah) / 2
    return 540 - tengah_x * skala, 1300 - tengah_y * skala, skala


def main() -> int:
    from papan_buat import buat_html
    from playwright.sync_api import sync_playwright
    from newmotion.application.katalog_renderer import katalog

    ukuran = json.loads(UKURAN.read_text(encoding="utf-8")) if UKURAN.is_file() else {}
    daftar = sorted(katalog())
    shot = []
    manifest = []
    for i, nama in enumerate(daftar):
        info = katalog()[nama]
        tambahan, parameter, nilai = keadaan(nama, info)
        tambahan.update(PROPERTI_UJI.get(nama, {}))
        x, y, skala = penempatan(ukuran.get(nama))
        shot.append({
            "at": i * DURASI, "horizon": 1990, "palet": "pagi", "debu": 0,
            "langit": 0, "kamera": {"z": 1, "x": 540, "y": 960},
            "benda": [{"jenis": nama, "x": x, "y": y, "s": skala, **tambahan}],
        })
        manifest.append({
            "jenis": nama, "parameter_animasi": parameter, "nilai": nilai,
            "ukuran_tercatat": nama in ukuran, "skala": round(skala, 4),
        })

    spek = {
        "latar": "gelap", "musik": False, "stempel": False, "dekor": False,
        "durasi": DURASI * len(shot), "cerita": {"shot": shot},
    }
    html = AKAR / "hasil_lembar_semua_benda.html"
    html.write_text(buat_html(spek, str(AKAR / "mesin-video" / "papan"), sudah_dijaga=True), encoding="utf-8")
    ubin = []
    galat_js: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": LEBAR, "height": TINGGI}, device_scale_factor=1)
        page.on("pageerror", lambda error: galat_js.append(str(error)))
        page.goto("file://" + str(html.resolve()))
        page.wait_for_timeout(400)
        for i, nama in enumerate(daftar):
            panel = []
            for offset in (0.6, 2.8):
                page.evaluate(f"setT({i * DURASI + offset})")
                if page.locator(f'g[data-j="{nama}"]').count() == 0:
                    galat_js.append(f"{nama}: elemen renderer tidak ditemukan")
                mentah = page.screenshot(clip={
                    "x": POTONG[0], "y": POTONG[1],
                    "width": POTONG[2] - POTONG[0], "height": POTONG[3] - POTONG[1],
                })
                gambar = Image.open(io.BytesIO(mentah)).convert("RGB")
                panel.append(gambar.resize(UKURAN_PANEL))
            ubin.append((nama, panel))
        browser.close()
    html.unlink(missing_ok=True)

    baris = math.ceil(len(ubin) / KOLUM)
    kanvas = Image.new("RGB", (KOLUM * LEBAR_KOTAK, baris * TINGGI_KOTAK), "#f3eee5")
    gambar = ImageDraw.Draw(kanvas)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 13)
        tebal = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
    except OSError:
        font = tebal = ImageFont.load_default()
    for i, (nama, panel) in enumerate(ubin):
        x, y = (i % KOLUM) * LEBAR_KOTAK, (i // KOLUM) * TINGGI_KOTAK
        gambar.text((x + 8, y + 5), nama, fill="#17130f", font=tebal)
        kanvas.paste(panel[0], (x + 8, y + 24))
        kanvas.paste(panel[1], (x + 190, y + 24))
        gambar.text((x + 8, y + 182), "awal", fill="#17130f", font=font)
        gambar.text((x + 190, y + 182), "akhir", fill="#17130f", font=font)

    keluar = AKAR / "hasil" / "lembar-semua-benda.png"
    keluar.parent.mkdir(parents=True, exist_ok=True)
    kanvas.save(keluar)
    (keluar.parent / "manifest-renderer.json").write_text(
        json.dumps({"jumlah_benda": len(daftar), "benda": manifest, "galat_javascript": galat_js},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"{len(daftar)} jenis benda, dua keadaan per jenis: {keluar}")
    if galat_js:
        raise RuntimeError("Galat JavaScript saat render: " + "; ".join(galat_js[:5]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
