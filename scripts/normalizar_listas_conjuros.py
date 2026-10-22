#!/usr/bin/env python3
"""Normaliza listas de conjuros y tablas partidas por maquetación."""

from __future__ import annotations
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SEP=re.compile(r"^:?-{3,}:?$")

def cells(line):
    s=line.strip()
    if not (s.startswith("|") and s.endswith("|")): return []
    return [x.strip() for x in s[1:-1].split("|")]

def is_sep(cs):
    return bool(cs) and all(SEP.match(x.replace(" ","")) for x in cs)

def norm(s):
    return re.sub(r"\s+"," ",s).strip().casefold()

def mark_semantic_labels(text):
    text=re.sub(
        r"^(Trucos \(conjuros de .+ de nivel 0\)|Conjuros de .+ de nivel [1-9])$",
        r"### \1", text, flags=re.MULTILINE
    )
    text=re.sub(
        r"^(Terreno (?:árido|polar|templado|tropical))$",
        r"#### \1", text, flags=re.MULTILINE
    )
    return text

def merge_adjacent_tables(text):
    lines=text.splitlines()
    out=[]
    i=0
    changes=0
    while i < len(lines):
        h=cells(lines[i]) if i<len(lines) else []
        sep=cells(lines[i+1]) if i+1<len(lines) else []
        if not (h and sep and len(h)==len(sep) and is_sep(sep)):
            out.append(lines[i]); i+=1; continue

        block=[lines[i],lines[i+1]]
        j=i+2
        while j<len(lines):
            r=cells(lines[j])
            if not r or len(r)!=len(h): break
            block.append(lines[j]); j+=1

        # Buscar otra tabla idéntica separada solo por blancos.
        k=j
        while k<len(lines) and not lines[k].strip(): k+=1
        h2=cells(lines[k]) if k<len(lines) else []
        s2=cells(lines[k+1]) if k+1<len(lines) else []
        if h2 and s2 and [norm(x) for x in h2]==[norm(x) for x in h] and is_sep(s2):
            m=k+2; rows2=[]
            while m<len(lines):
                r=cells(lines[m])
                if not r or len(r)!=len(h2): break
                rows2.append(lines[m]); m+=1
            block.extend(rows2)
            out.extend(block)
            i=m
            changes+=1
        else:
            out.extend(block)
            i=j
    return "\n".join(out).rstrip()+"\n",changes

def main():
    files=0; merges=0
    for path in sorted((ROOT/"ES"/"Clases").glob("*.md")):
        old=path.read_text(encoding="utf-8")
        marked=mark_semantic_labels(old)
        new,n=merge_adjacent_tables(marked)
        if new!=old:
            path.write_text(new,encoding="utf-8")
            files+=1; merges+=n
            print(f"{path.relative_to(ROOT)}: fusiones={n}")
    print(f"Archivos modificados: {files}; fusiones: {merges}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
