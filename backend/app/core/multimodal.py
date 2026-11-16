import os
import re
import io
import base64
import httpx
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List
from PIL import Image
import pypdf
from app.schemas.organize import PlanItem

GENERIC_IMAGE_PATTERNS = [
    r"^screenshot.*",
    r"^captura.*",
    r"^img[_-].*",
    r"^dsc[_-].*",
    r"^whatsapp\s*image.*",
    r"^image.*",
    r"^screen\s*shot.*",
    r"^sin[_\s-]*t[ií]tulo.*",
    r"^pasted\s*image.*",
    r"^[0-9_\-\.\s]+$",
]

GENERIC_PDF_PATTERNS = [
    r"^download.*",
    r"^descarga.*",
    r"^documento?.*",
    r"^factura.*",
    r"^comprobante.*",
    r"^recibo.*",
    r"^scan.*",
    r"^file.*",
    r"^archivo.*",
    r"^[0-9_\-\.\s]+$",
]

def is_generic_filename(name: str, patterns: List[str]) -> bool:
    stem = Path(name).stem.lower().strip()
    return any(re.match(p, stem) for p in patterns)

def extract_pdf_text(pdf_path: Path, max_chars: int = 1500) -> str:
    """Extrae texto plano de la primera página del PDF de manera segura."""
    try:
        reader = pypdf.PdfReader(str(pdf_path))
        if len(reader.pages) == 0:
            return ""
        first_page = reader.pages[0]
        text = first_page.extract_text() or ""
        clean_text = " ".join(text.split())
        return clean_text[:max_chars]
    except Exception:
        return ""

def create_image_thumbnail_b64(img_path: Path, max_dim: int = 512) -> Tuple[str, str]:
    """Genera una miniatura JPEG optimizada en Base64 para visión multimodal."""
    try:
        with Image.open(img_path) as im:
            if im.mode in ("RGBA", "P", "LA"):
                im = im.convert("RGB")
            im.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=80)
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            return b64, "image/jpeg"
    except Exception:
        return "", ""

def sanitize_suggested_name(name: str, original_suffix: str) -> str:
    """Sanitiza el nombre generado asegurando extensión correcta y sin caracteres prohibidos."""
    clean = re.sub(r'[<>:"/\\|?*]', "", name).strip()
    clean = clean.replace(" ", "_")
    clean = re.sub(r"_+", "_", clean).strip("._")
    
    if not clean.lower().endswith(original_suffix.lower()):
        clean += original_suffix
    return clean

def heuristic_rename_pdf(orig_name: str, text: str) -> Optional[str]:
    """Deduce un nombre inteligente para un PDF usando expresiones regulares y entidades."""
    if not text:
        return None

    suffix = Path(orig_name).suffix
    lower_text = text.lower()

    # 1. Detectar tipo de documento
    doc_type = "Documento"
    if re.search(r"\b(factura\s+[abc]|factura)\b", lower_text):
        doc_type = "Factura"
    elif re.search(r"\b(comprobante\s+de\s+pago|comprobante\s+de\s+transferencia|comprobante)\b", lower_text):
        doc_type = "Comprobante"
    elif re.search(r"\b(recibo\s+de\s+sueldo|recibo)\b", lower_text):
        doc_type = "Recibo"
    elif re.search(r"\b(constancia\s+de\s+cuit|constancia\s+de\s+inscripci[oó]n|constancia)\b", lower_text):
        doc_type = "Constancia"
    elif re.search(r"\b(resumen\s+de\s+cuenta|resumen\s+de\s+tarjeta|resumen)\b", lower_text):
        doc_type = "Resumen"
    elif re.search(r"\b(trabajo\s+pr[aá]ctico|tp\s*\d+)\b", lower_text):
        doc_type = "TP"
    elif re.search(r"\b(parcial|examen)\b", lower_text):
        doc_type = "Examen"
    elif re.search(r"\b(seminario|apunte|gu[ií]a)\b", lower_text):
        doc_type = "Apunte"

    # 2. Detectar entidad / empresa / servicio
    entity = ""
    entities = [
        "Mercado Pago", "Mercado Libre", "EPEC", "Telecom", "Personal", "Claro",
        "Movistar", "Fibertel", "Flow", "Aguas Cordobesas", "AySA", "Metrogas", "Ecogas",
        "Galicia", "Santander", "BBVA", "Macro", "Banco Nacion", "Uala", "Lemon",
        "Brubank", "Naranja X", "AFIP", "ARCA", "ANSES", "Itec", "UTN", "Universidad"
    ]
    for ent in entities:
        if re.search(rf"\b{re.escape(ent.lower())}\b", lower_text):
            entity = ent.replace(" ", "")
            break

    # 3. Detectar período / mes / fecha
    period = ""
    months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    for m in months:
        if re.search(rf"\b{m.lower()}\b", lower_text):
            year_match = re.search(r"\b(202[0-9])\b", text)
            year = year_match.group(1) if year_match else ""
            period = f"{m}_{year}" if year else m
            break

    if not period:
        date_match = re.search(r"\b(\d{2})[/\-](\d{2})[/\-](202[0-9])\b", text)
        if date_match:
            period = f"{date_match.group(3)}-{date_match.group(2)}-{date_match.group(1)}"

    # Si encontramos al menos doc_type y entidad
    if entity:
        parts = [doc_type, entity]
        if period:
            parts.append(period)
        return sanitize_suggested_name("_".join(parts), suffix)

    # Si encontramos palabras prominentes de estudio
    study_match = re.search(r"\b(seminario\s+ia|programaci[oó]n\s+ii|algoritmos|base\s+de\s+datos)\b", lower_text)
    if study_match:
        subject = study_match.group(1).title().replace(" ", "_")
        return sanitize_suggested_name(f"{doc_type}_{subject}", suffix)

    return None

def heuristic_rename_image(orig_name: str, img_path: Path) -> Optional[str]:
    """Genera un nombre descriptivo para capturas o fotos genéricas según metadatos."""
    suffix = Path(orig_name).suffix
    try:
        stat = img_path.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime)
        timestamp_str = mtime.strftime("%Y-%m-%d_%H-%M")
    except Exception:
        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M")

    stem_lower = Path(orig_name).stem.lower()
    if "screenshot" in stem_lower or "captura" in stem_lower or "screen" in stem_lower:
        return sanitize_suggested_name(f"Captura_{timestamp_str}", suffix)
    elif "img" in stem_lower or "dsc" in stem_lower or "whatsapp" in stem_lower:
        return sanitize_suggested_name(f"Foto_{timestamp_str}", suffix)
    return None

async def ai_rename_pdf_content(orig_name: str, text: str, provider: str, model: Optional[str] = None, api_key: Optional[str] = None) -> Optional[str]:
    """Pide a la IA un nombre conciso a partir del texto de la primera página."""
    if not text:
        return None

    prompt = (
        "A partir del siguiente texto de la primera página de un documento, devuelve ÚNICAMENTE "
        "un nombre de archivo muy claro y descriptivo (ej: Factura_EPEC_Noviembre_2026, Constancia_Inscripcion_AFIP, "
        "Trabajo_Practico_Seminario_IA). Máximo 4 a 5 palabras unidas por guiones bajos, sin extensión, sin comillas ni markdown:\n\n"
        + text[:1000]
    )

    suffix = Path(orig_name).suffix

    if provider == "gemini" and api_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model or 'gemini-1.5-flash'}:generateContent?key={api_key}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
                if res.status_code == 200:
                    raw = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    cleaned = re.sub(r'[`"\'\n]', "", raw).strip()
                    return sanitize_suggested_name(cleaned, suffix)
        except Exception:
            pass

    return heuristic_rename_pdf(orig_name, text)

async def ai_rename_image_vision(orig_name: str, img_path: Path, provider: str, model: Optional[str] = None, api_key: Optional[str] = None) -> Optional[str]:
    """Usa visión de Gemini o heurística para describir una imagen."""
    suffix = Path(orig_name).suffix
    b64, mime = create_image_thumbnail_b64(img_path)

    if provider == "gemini" and api_key and b64:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model or 'gemini-1.5-flash'}:generateContent?key={api_key}"
            prompt = (
                "Observa esta imagen y devuelve ÚNICAMENTE un nombre de archivo muy conciso y descriptivo en español "
                "(ej: Diagrama_Arquitectura_Cloud, Error_Terminal_Python, Comprobante_Transferencia_Bancaria). "
                "Máximo 3 a 5 palabras separadas por guiones bajos, sin extensión, sin comillas ni markdown."
            )
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {"inline_data": {"mime_type": mime, "data": b64}}
                        ]
                    }
                ]
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    raw = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    cleaned = re.sub(r'[`"\'\n]', "", raw).strip()
                    return sanitize_suggested_name(cleaned, suffix)
        except Exception:
            pass

    return heuristic_rename_image(orig_name, img_path)

async def apply_multimodal_renaming(
    items: List[PlanItem],
    provider: str = "smart_rules",
    model: Optional[str] = None,
    api_key: Optional[str] = None
) -> List[PlanItem]:
    """Analiza los elementos del plan y actualiza suggested_name si amerita renombrado multimodal."""
    for item in items:
        p = Path(item.original_path)
        if not p.exists():
            continue

        ext = p.suffix.lower()

        # Caso PDF
        if ext == ".pdf":
            # Solo renombrar si tiene nombre genérico o poco descriptivo
            if is_generic_filename(item.original_name, GENERIC_PDF_PATTERNS) or len(p.stem) < 8:
                text = extract_pdf_text(p)
                if text:
                    new_name = await ai_rename_pdf_content(item.original_name, text, provider, model, api_key)
                    if new_name and new_name.lower() != item.original_name.lower():
                        item.suggested_name = new_name
                        item.reason += " | ✨ Renombrado inteligente por lectura de PDF"

        # Caso Imágenes
        elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
            if is_generic_filename(item.original_name, GENERIC_IMAGE_PATTERNS):
                new_name = await ai_rename_image_vision(item.original_name, p, provider, model, api_key)
                if new_name and new_name.lower() != item.original_name.lower():
                    item.suggested_name = new_name
                    item.reason += " | ✨ Renombrado inteligente por visión multimodal"

    return items
