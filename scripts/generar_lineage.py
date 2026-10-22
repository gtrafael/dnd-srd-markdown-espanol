#!/usr/bin/env python3
"""Genera lineage Markdown -> páginas PDF -> jerarquía oficial.

El mapeo usa n-gramas por página para localizar dónde aparece cada archivo.
No escribe metadatos dentro del texto de entrenamiento; genera un sidecar JSON.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import fitz


def norm(s: str) -> list[str]:
    s = unicodedata.normalize("NFKC", s).lower()
    s = re.sub(r"[^\wáéíóúüñ]+", " ", s, flags=re.UNICODE)
    return [x for x in s.split() if x]


def quitar_markdown(s: str) -> str:
    s = re.sub(r"^---\n[\s\S]*?\n---\n", "", s)
    s = re.sub(r"~~~[\s\S]*?~~~", " ", s)
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"\[\[([^\]|]+\|)?([^\]]+)\]\]", r"\2", s)
    s = re.sub(r"[#*_>~|]", " ", s)
    return s


def ngrams(tokens: list[str], n: int = 5) -> list[tuple[str, ...]]:
    if len(tokens) < n:
        return []
    return [tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1)]


def pdf_paginas(doc: fitz.Document):
    paginas = []
    inv = defaultdict(set)
    for i, page in enumerate(doc):
        ts = norm(page.get_text("text"))
        paginas.append(ts)
        for ng in set(ngrams(ts, 5)):
            inv[ng].add(i+1)
    return paginas, inv


def toc(doc: fitz.Document) -> list[dict]:
    raw = doc.get_toc(simple=True)
    out = []
    stack: list[str] = []
    for nivel, titulo, pagina in raw:
        nivel = max(1, int(nivel))
        stack = stack[:nivel-1]
        stack.append(str(titulo).strip())
        out.append({
            "nivel": nivel,
            "titulo": str(titulo).strip(),
            "pagina": int(pagina),
            "jerarquia": list(stack),
        })
    return out


def toc_desde_indice(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out: list[dict] = []

    def walk(obj: dict, nivel: int, padres: list[str]) -> None:
        for titulo, meta in obj.items():
            if not isinstance(meta, dict) or "page" not in meta:
                continue
            jerarquia = padres + [titulo]
            out.append({
                "nivel": nivel,
                "titulo": titulo,
                "pagina": int(meta["page"]),
                "jerarquia": jerarquia,
            })
            children = meta.get("children")
            if isinstance(children, dict):
                walk(children, nivel + 1, jerarquia)

    walk(data, 1, [])
    return out


def jerarquia_para_pagina(items: list[dict], pagina: int) -> list[str]:
    activa: list[str] = []
    for item in items:
        if item["pagina"] > pagina:
            break
        nivel = item["nivel"]
        activa = activa[:nivel-1]
        activa.append(item["titulo"])
    return activa


def titulo_md(texto: str, fallback: str) -> str:
    for linea in texto.splitlines():
        m = re.match(r"^#{1,6}\s+(.+?)\s*$", linea)
        if m:
            return re.sub(r"[*_]", "", m.group(1)).strip()
    return fallback


def mapear_archivo(path: Path, raiz: Path, inv, toc_items: list[dict]) -> dict:
    raw = path.read_text(encoding="utf-8")
    texto = quitar_markdown(raw)
    ts = norm(texto)
    ngs = ngrams(ts, 5)
    conteo: Counter[int] = Counter()
    for ng in set(ngs):
        for pagina in inv.get(ng, ()):
            conteo[pagina] += 1

    denom = max(1, len(set(ngs)))
    ranking = [
        {"pagina": p, "coincidencias": n, "score": round(n/denom, 5)}
        for p,n in conteo.most_common(12)
    ]

    paginas = []
    if ranking:
        max_score = ranking[0]["score"]
        umbral = max(0.015, max_score * 0.18)
        paginas = sorted(
            r["pagina"] for r in ranking
            if r["score"] >= umbral and r["coincidencias"] >= 2
        )

    titulo = titulo_md(raw, path.stem)
    origen_mapeo = "ngram"

    # Los archivos muy breves (por ejemplo una introducción de capítulo) pueden
    # no producir suficientes 5-gramas. Si no hay evidencia textual, aceptamos
    # como fallback únicamente un título exacto y único del TOC/índice oficial.
    if not paginas:
        titulo_norm = " ".join(norm(titulo))
        candidatos_toc = [
            item for item in toc_items
            if " ".join(norm(str(item.get("titulo", "")))) == titulo_norm
        ]
        if len(candidatos_toc) == 1:
            paginas = [int(candidatos_toc[0]["pagina"])]
            origen_mapeo = "titulo_toc"

    estado = "ok"
    if not paginas:
        estado = "sin_mapear"
    elif origen_mapeo == "ngram" and ranking and ranking[0]["score"] < 0.03:
        estado = "debil"

    primera = paginas[0] if paginas else None
    return {
        "archivo": str(path.relative_to(raiz)),
        "titulo": titulo,
        "paginas_pdf": paginas,
        "pagina_principal": primera,
        "jerarquia_pdf": jerarquia_para_pagina(toc_items, primera) if primera else [],
        "estado": estado,
        "origen_mapeo": origen_mapeo,
        "ranking_paginas": ranking[:8],
    }


def idioma(corpus: Path, pdf: Path, nombre: str, indice: Path | None = None) -> dict:
    doc = fitz.open(pdf)
    _, inv = pdf_paginas(doc)
    toc_items = toc_desde_indice(indice) if indice else toc(doc)
    archivos = [mapear_archivo(path, corpus, inv, toc_items) for path in sorted(corpus.rglob("*.md"))]
    estados = Counter(x["estado"] for x in archivos)
    return {
        "idioma": nombre,
        "pdf": pdf.name,
        "toc": toc_items,
        "resumen": dict(estados),
        "archivos": archivos,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--pdf-es", type=Path, required=True)
    ap.add_argument("--pdf-en", type=Path, required=True)
    ap.add_argument("--salida", type=Path, required=True)
    ap.add_argument("--indice-es", type=Path)
    ap.add_argument("--indice-en", type=Path)
    args = ap.parse_args()
    out = {
        "es": idioma(args.corpus/"es", args.pdf_es, "es", args.indice_es),
        "en": idioma(args.corpus/"en", args.pdf_en, "en", args.indice_en),
    }
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(out, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
