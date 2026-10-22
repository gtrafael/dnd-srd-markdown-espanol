#!/usr/bin/env python3
"""Mide cobertura inversa PDF -> corpus para descubrir omisiones.

A diferencia de validar_corpus_con_pdf.py, aquí la pregunta es:
"¿qué parte del texto oficial no aparece representada en el corpus?"

Se calculan recalls de trigramas y 5-gramas por página. Las tablas y el orden
multicolumna pueden reducir la métrica, por lo que el resultado es detector de
riesgo, no criterio automático de corrección.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

import fitz


def normalizar(texto: str) -> list[str]:
    texto = unicodedata.normalize("NFKC", texto).lower()
    texto = texto.replace("\u00ad", "")
    texto = re.sub(r"system reference document 5\.2\.1", " ", texto)
    texto = re.sub(r"\b\d{1,3}\b(?=\s*$)", " ", texto, flags=re.MULTILINE)
    texto = re.sub(r"[^\wáéíóúüñ]+", " ", texto, flags=re.UNICODE)
    return [x for x in texto.split() if x]


def limpiar_markdown(texto: str) -> str:
    texto = re.sub(r"^---\n[\s\S]*?\n---\n", "", texto)
    texto = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", texto)
    texto = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", texto)
    texto = re.sub(r"\[\[([^\]|]+\|)?([^\]]+)\]\]", r"\2", texto)
    texto = re.sub(r"[#*_>~|]", " ", texto)
    return texto


def ngrams(tokens: list[str], n: int) -> set[tuple[str, ...]]:
    if len(tokens) < n:
        return set()
    return {tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1)}


def corpus_grams(root: Path) -> dict[int, set[tuple[str, ...]]]:
    tokens: list[str] = []
    for p in sorted(root.rglob("*.md")):
        tokens.extend(normalizar(limpiar_markdown(p.read_text(encoding="utf-8"))))
        # Barrera entre archivos: evita crear n-gramas artificiales entre notas.
        tokens.extend(["__archivo__", "__archivo__", "__archivo__", "__archivo__"])
    return {3: ngrams(tokens, 3), 5: ngrams(tokens, 5)}


def recall(ref: set, corpus: set) -> float:
    if not ref:
        return 1.0
    return len(ref & corpus) / len(ref)


def paginas(pdf: Path, corpus: Path) -> list[dict]:
    cg = corpus_grams(corpus)
    doc = fitz.open(pdf)
    out = []
    for i, page in enumerate(doc, 1):
        toks = normalizar(page.get_text("text"))
        g3, g5 = ngrams(toks, 3), ngrams(toks, 5)
        out.append({
            "pagina": i,
            "tokens": len(toks),
            "recall_3gram_pdf_a_corpus": round(recall(g3, cg[3]), 5),
            "recall_5gram_pdf_a_corpus": round(recall(g5, cg[5]), 5),
        })
    return out


def tramos_toc(toc: list[dict], page_metrics: list[dict]) -> list[dict]:
    # Solo niveles 2 y 3: capítulos/secciones suficientemente grandes para QA.
    sel=[x for x in toc if int(x.get("nivel",99)) in (2,3)]
    total_paginas=len(page_metrics)
    out=[]
    for i,item in enumerate(sel):
        ini=int(item["pagina"])
        # El final es la página previa al siguiente elemento del mismo o menor nivel.
        fin=total_paginas
        for sig in sel[i+1:]:
            if int(sig["nivel"]) <= int(item["nivel"]):
                fin=max(ini,int(sig["pagina"])-1)
                break
        subset=[x for x in page_metrics if ini <= x["pagina"] <= fin]
        if not subset: continue
        # Promedio ponderado aproximado por tokens.
        peso=sum(max(1,x["tokens"]) for x in subset)
        r3=sum(x["recall_3gram_pdf_a_corpus"]*max(1,x["tokens"]) for x in subset)/peso
        r5=sum(x["recall_5gram_pdf_a_corpus"]*max(1,x["tokens"]) for x in subset)/peso
        out.append({
            "nivel":item["nivel"],
            "titulo":item["titulo"],
            "jerarquia":item.get("jerarquia",[]),
            "pagina_inicio":ini,
            "pagina_fin":fin,
            "recall_3gram_pdf_a_corpus":round(r3,5),
            "recall_5gram_pdf_a_corpus":round(r5,5),
        })
    return out


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--corpus",type=Path,required=True)
    ap.add_argument("--pdf-es",type=Path,required=True)
    ap.add_argument("--pdf-en",type=Path,required=True)
    ap.add_argument("--lineage",type=Path,required=True)
    ap.add_argument("--salida",type=Path,required=True)
    a=ap.parse_args()

    lin=json.loads(a.lineage.read_text(encoding="utf-8"))
    out={}
    for lang,pdf in (("es",a.pdf_es),("en",a.pdf_en)):
        ps=paginas(pdf,a.corpus/lang)
        tr=tramos_toc(lin[lang]["toc"],ps)
        out[lang]={
            "paginas":ps,
            "tramos":tr,
            "paginas_menor_cobertura":sorted(
                [x for x in ps if x["tokens"]>=80],
                key=lambda x:x["recall_5gram_pdf_a_corpus"]
            )[:40],
            "tramos_menor_cobertura":sorted(
                tr,key=lambda x:x["recall_5gram_pdf_a_corpus"]
            )[:30],
        }

    a.salida.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for lang in ("es","en"):
        print(lang,"peores páginas",out[lang]["paginas_menor_cobertura"][:10])
        print(lang,"peores tramos",out[lang]["tramos_menor_cobertura"][:10])
    return 0

if __name__=="__main__":
    raise SystemExit(main())
