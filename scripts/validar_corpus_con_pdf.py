#!/usr/bin/env python3
"""Compara el corpus curado con el texto de los PDF oficiales."""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import tempfile
import unicodedata
from collections import Counter
from pathlib import Path

TOKENS_FUERA_PDF_PERMITIDOS_ES = {
    ("abreviatura", "GlosarioDeReglas/ConvencionesDelGlosario.md"),
    ("encarnan", "Clases/Paladin.md"),
    ("asegura", "ComoJugar/ElRitmoDeJuego.md"),
    ("tratado", "Conjuros/DescripcionesDeConjuros/PolimorfarVerdadero.md"),
    ("parpadeantes", "Conjuros/DescripcionesDeConjuros/RociadaDeColor.md"),
    ("susurrará", "ObjetosMagicos/ObjetosMagicosDeLaAALaZ/ArcoJuramentado.md"),
}


def texto_pdf(pdf: Path) -> str:
    with tempfile.NamedTemporaryFile(suffix=".txt") as tmp:
        subprocess.run(["pdftotext", str(pdf), tmp.name], check=True)
        return Path(tmp.name).read_text(encoding="utf-8", errors="replace")


def quitar_formato_markdown(texto: str) -> str:
    lineas = []
    for linea in texto.splitlines():
        stripped = linea.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            continue
        lineas.append(linea)
    texto = "\n".join(lineas)
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", texto)
    texto = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", texto)
    texto = texto.replace("#", " ").replace("*", " ").replace("_", " ")
    texto = texto.replace("~", " ").replace(">", " ")
    return html.unescape(texto)


def tokens(texto: str) -> list[str]:
    texto = unicodedata.normalize("NFC", texto).lower()
    return re.findall(r"[a-záéíóúüñ0-9]+", texto)


def normalizar_pdf(texto: str) -> list[str]:
    texto = unicodedata.normalize("NFC", texto).replace("\u00ad", "")
    texto = re.sub(
        r"(?<=[A-Za-zÁÉÍÓÚÜÑáéíóúüñ])(?:-|\u2011)\s*\n\s*(?=[A-Za-zÁÉÍÓÚÜÑáéíóúüñ])",
        "",
        texto,
    )
    texto = re.sub(
        r"(?mi)^\s*Documento de referencia del sistema 5\.2\.1\s*$",
        " ",
        texto,
    )
    texto = re.sub(r"(?m)^\s*\d{1,3}\s*$", " ", texto)
    return tokens(texto)


def shingles(lista: list[str], n: int) -> set[tuple[str, ...]]:
    if len(lista) < n:
        return set()
    return {tuple(lista[i:i+n]) for i in range(len(lista) - n + 1)}


def celdas_tabla(linea: str) -> tuple[str, ...] | None:
    linea = linea.strip()
    if not (linea.startswith("|") and linea.endswith("|")):
        return None
    return tuple(celda.strip() for celda in linea[1:-1].split("|"))


def es_separador_tabla(linea: str) -> bool:
    celdas = celdas_tabla(linea)
    return bool(celdas) and all(
        re.fullmatch(r":?-{3,}:?", celda.replace(" ", "")) for celda in celdas
    )


def tablas_continuadas_residuales(texto: str) -> list[tuple[str, ...]]:
    lineas = texto.splitlines()
    cabecera_actual: tuple[str, ...] | None = None
    hallazgos: list[tuple[str, ...]] = []
    i = 0
    while i < len(lineas):
        if (
            celdas_tabla(lineas[i]) is not None
            and i + 1 < len(lineas)
            and es_separador_tabla(lineas[i + 1])
        ):
            cabecera_actual = celdas_tabla(lineas[i])
            i += 2
            continue
        if (
            lineas[i] == ""
            and cabecera_actual is not None
            and i + 2 < len(lineas)
            and celdas_tabla(lineas[i + 1]) == cabecera_actual
            and es_separador_tabla(lineas[i + 2])
        ):
            hallazgos.append(cabecera_actual)
            i += 3
            continue
        if lineas[i] and celdas_tabla(lineas[i]) is None:
            cabecera_actual = None
        i += 1
    return hallazgos


def validar_idioma(corpus: Path, pdf: Path, idioma: str) -> dict:
    pdf_tokens = normalizar_pdf(texto_pdf(pdf))
    vocab_pdf = set(pdf_tokens)
    pdf_3 = shingles(pdf_tokens, 3)
    pdf_5 = shingles(pdf_tokens, 5)

    alertas = []
    fuera_pdf = Counter()
    ejemplos_fuera_pdf: dict[str, list[str]] = {}
    patrones_sospechosos = []
    total_3 = total_5 = encontrados_3 = encontrados_5 = 0

    for ruta in sorted(corpus.rglob("*.md")):
        texto_md = ruta.read_text(encoding="utf-8")
        relativo = str(ruta.relative_to(corpus))
        ts = tokens(quitar_formato_markdown(texto_md))

        if idioma == "es":
            permitidos = {"valor", "mod", "salv", "game", "master"}
            for token in tokens(texto_md):
                if len(token) >= 4 and token not in vocab_pdf and token not in permitidos:
                    if (token, relativo) in TOKENS_FUERA_PDF_PERMITIDOS_ES:
                        continue
                    fuera_pdf[token] += 1
                    ejemplos_fuera_pdf.setdefault(token, [])
                    if relativo not in ejemplos_fuera_pdf[token] and len(ejemplos_fuera_pdf[token]) < 3:
                        ejemplos_fuera_pdf[token].append(relativo)

            patrones = {
                "diaeresis_a": r"ä",
                "puntuacion_sin_espacio": r"[\.,;:!?][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]",
                "palabra_numero_pegados": r"\b[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{2,}\d+[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]*\b",
                "dado_con_o": r"\b\d+d\d*[oO]\b",
                "numero_unidad_pegados": r"\b\d+(?:,\d+)?[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{1,}\b",
                "salto_parrafo_en_mitad_oracion": r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ,]\n\n[a-záéíóúüñ]",
            }
            for nombre, patron in patrones.items():
                coincidencias = sorted(set(re.findall(patron, texto_md)))
                if coincidencias:
                    patrones_sospechosos.append({
                        "archivo": relativo,
                        "tipo": nombre,
                        "muestras": coincidencias[:8],
                    })

            continuaciones = tablas_continuadas_residuales(texto_md)
            if continuaciones:
                patrones_sospechosos.append({
                    "archivo": relativo,
                    "tipo": "tabla_continuada_con_cabecera_repetida",
                    "muestras": [" | ".join(c) for c in continuaciones[:8]],
                })
        s3 = shingles(ts, 3)
        s5 = shingles(ts, 5)
        e3 = len(s3 & pdf_3)
        e5 = len(s5 & pdf_5)
        total_3 += len(s3)
        total_5 += len(s5)
        encontrados_3 += e3
        encontrados_5 += e5
        recall3 = e3 / len(s3) if s3 else 1.0
        recall5 = e5 / len(s5) if s5 else 1.0
        if len(s5) >= 30 and recall5 < 0.80:
            alertas.append({
                "archivo": relativo,
                "tokens": len(ts),
                "recall_3gram": round(recall3, 4),
                "recall_5gram": round(recall5, 4),
            })

    alertas.sort(key=lambda x: x["recall_5gram"])
    resultado = {
        "idioma": idioma,
        "tokens_pdf": len(pdf_tokens),
        "recall_global_3gram": round(encontrados_3 / total_3, 5) if total_3 else 1.0,
        "recall_global_5gram": round(encontrados_5 / total_5, 5) if total_5 else 1.0,
        "archivos_bajo_umbral_5gram": alertas,
    }
    if idioma == "es":
        resultado["patrones_sospechosos"] = patrones_sospechosos
        resultado["tokens_fuera_pdf"] = [
            {
                "token": token,
                "apariciones": cantidad,
                "archivos": ejemplos_fuera_pdf[token],
            }
            for token, cantidad in fuera_pdf.most_common(250)
        ]
    return resultado


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", type=Path, required=True)
    p.add_argument("--pdf-es", type=Path, required=True)
    p.add_argument("--pdf-en", type=Path, required=True)
    p.add_argument("--salida", type=Path, required=True)
    args = p.parse_args()

    informe = {
        "metodo": "Comparación de n-gramas de prosa normalizada; las tablas se revisan por separado.",
        "es": validar_idioma(args.corpus / "es", args.pdf_es, "es"),
        "en": validar_idioma(args.corpus / "en", args.pdf_en, "en"),
    }
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    errores = []
    if informe["es"].get("patrones_sospechosos"):
        errores.append(
            f"{len(informe['es']['patrones_sospechosos'])} patrones sospechosos en ES"
        )
    if informe["es"].get("tokens_fuera_pdf"):
        muestras = "; ".join(
            f"{item['token']} ({', '.join(item['archivos'])})"
            for item in informe["es"]["tokens_fuera_pdf"][:10]
        )
        errores.append(
            f"{len(informe['es']['tokens_fuera_pdf'])} tokens ES no verificados contra el PDF: "
            + muestras
        )
    if errores:
        raise SystemExit("QA del corpus no superado: " + "; ".join(errores))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
