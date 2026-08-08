"""FASE 6 (2026-08-08) — Test puri: validazione upload avatar.

La difesa chiave è `sniff_image_ext`: accetta il file SOLO se i magic
bytes reali e il Content-Type dichiarato concordano (PNG/JPEG/WEBP).
Nessun Mongo richiesto (--noconftest).
"""
from app.avatars import MAX_AVATAR_BYTES, sniff_image_ext

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 200
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 200
WEBP = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"\x00" * 200
SVG = b"<svg xmlns='http://www.w3.org/2000/svg'></svg>"


def test_formati_validi_accettati():
    assert sniff_image_ext(PNG, "image/png") == "png"
    assert sniff_image_ext(JPG, "image/jpeg") == "jpg"
    assert sniff_image_ext(WEBP, "image/webp") == "webp"


def test_content_type_e_magic_devono_concordare():
    # Un PNG spacciato per JPEG (o viceversa) viene rifiutato.
    assert sniff_image_ext(PNG, "image/jpeg") is None
    assert sniff_image_ext(JPG, "image/png") is None


def test_svg_sempre_rifiutato():
    """SVG = rischio XSS: mai accettato, con qualsiasi Content-Type."""
    assert sniff_image_ext(SVG, "image/svg+xml") is None
    assert sniff_image_ext(SVG, "image/png") is None


def test_formati_sconosciuti_rifiutati():
    assert sniff_image_ext(b"GIF89a" + b"\x00" * 50, "image/gif") is None
    assert sniff_image_ext(b"\x00" * 50, "application/octet-stream") is None
    assert sniff_image_ext(PNG, "") is None


def test_content_type_con_parametri():
    assert sniff_image_ext(PNG, "image/png; charset=binary") == "png"


def test_cap_dimensione_ragionevole():
    assert MAX_AVATAR_BYTES == 2 * 1024 * 1024
