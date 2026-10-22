#!/usr/bin/env python3
"""Detecta solapamientos semánticos fuertes entre archivos del corpus.

Objetivo: evitar entrenar dos veces el mismo contenido porque el repo fuente
contenga una nota agregada y varias notas hoja (por ejemplo, un capítulo
completo y sus subsecciones por separado).
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


def limpiar(texto: str) -> str:
    texto = re.sub(r"^---\n[\s\S]*?\n---\n", "", texto)
    texto = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", texto)
    texto = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", texto)
    texto = re.sub(r"\[\[([^\]|]+\|)?([^\]]+)\]\]", r"\2", texto)
    texto = re.sub(r"[#*_>~|]", " ", texto)
    texto = unicodedata.normalize("NFKC", texto).lower()
    texto = re.sub(r"[^\wáéíóúüñ]+", " ", texto, flags=re.UNICODE)
    return texto


def grams(texto: str, n: int = 5) -> set[tuple[str, ...]]:
    ts = texto.split()
    if len(ts) < n:
        return set()
    return {tuple(ts[i:i+n]) for i in range(len(ts)-n+1)}


def auditar(root: Path) -> dict:
    docs={}
    inv=defaultdict(list)
    for p in sorted(root.rglob("*.md")):
        rel=p.relative_to(root).as_posix()
        g=grams(limpiar(p.read_text(encoding="utf-8")))
        docs[rel]=g
        for x in g:
            inv[x].append(rel)

    compartidos=Counter()
    for files in inv.values():
        if len(files)<2 or len(files)>20:
            continue
        files=sorted(set(files))
        for i,a in enumerate(files):
            for b in files[i+1:]:
                compartidos[(a,b)]+=1

    pares=[]
    for (a,b),inter in compartidos.items():
        ga,gb=docs[a],docs[b]
        if not ga or not gb:
            continue
        ca=inter/len(ga)
        cb=inter/len(gb)
        jac=inter/len(ga|gb)
        pequeno=a if len(ga)<=len(gb) else b
        grande=b if pequeno==a else a
        containment=max(ca,cb)
        # >=80% del archivo pequeño dentro del grande, con suficiente texto.
        if containment>=0.80 and min(len(ga),len(gb))>=20:
            pares.append({
                "archivo_a":a,"archivo_b":b,
                "5grams_a":len(ga),"5grams_b":len(gb),
                "5grams_comunes":inter,
                "containment_a":round(ca,5),
                "containment_b":round(cb,5),
                "jaccard":round(jac,5),
                "archivo_probablemente_redundante":pequeno,
                "archivo_contenedor":grande,
            })

    pares.sort(key=lambda x:(-max(x["containment_a"],x["containment_b"]),-x["5grams_comunes"]))
    candidatos=Counter(x["archivo_probablemente_redundante"] for x in pares)
    return {
        "archivos":len(docs),
        "pares_solapamiento_fuerte":pares,
        "candidatos_redundantes":[
            {"archivo":a,"pares":n} for a,n in candidatos.most_common()
        ],
    }


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--corpus",type=Path,required=True)
    ap.add_argument("--salida",type=Path,required=True)
    a=ap.parse_args()
    out={lang:auditar(a.corpus/lang) for lang in ("es","en")}
    a.salida.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for lang in ("es","en"):
        print(lang,"pares",len(out[lang]["pares_solapamiento_fuerte"]))
        print(lang,"candidatos",out[lang]["candidatos_redundantes"][:20])
    return 0

if __name__=="__main__":
    raise SystemExit(main())
