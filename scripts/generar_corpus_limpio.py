#!/usr/bin/env python3
"""Convierte custom/main en la variante limpia destinada a dungeon-agent.

Se ejecuta sobre una copia/worktree de custom/main.
No corrige contenido: custom/main debe estar corregida antes.
"""

from __future__ import annotations
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

EXCLUIR={
    "ES/Espanol.md","EN/English.md",
    "EN/Animals/Animals.md","EN/Monsters/Monsters.md",
    "EN/Spells/Spells.md","EN/Treasure/Treasure.md",
    "EN/Gamemastering/Objects.md","EN/Equipment/Trade Goods.md",
}

def quitar_frontmatter(t:str)->str:
    if not t.startswith("---\n"): return t
    end=t.find("\n---\n",4)
    return t[end+5:] if end>=0 else t

def wikilinks(t:str)->str:
    def repl(m):
        x=m.group(1)
        if "|" in x:return x.rsplit("|",1)[1]
        return x.rsplit("/",1)[-1]
    return re.sub(r"\[\[([^\]]+)\]\]",repl,t)

def limpiar(t:str)->str:
    t=quitar_frontmatter(t)
    t=wikilinks(t)
    t=re.sub(r"!\[[^\]]*\]\([^)]*\)","",t)
    t=re.sub(r"<img\b[^>]*>","",t,flags=re.I)
    t="\n".join(x.rstrip() for x in t.splitlines())
    t=re.sub(r"\n{3,}","\n\n",t)
    return t.strip()+"\n"

def canonico(p:Path)->bool:
    rel=p.relative_to(ROOT).as_posix()
    if rel in EXCLUIR:return False
    if any("(Alt)" in x for x in p.relative_to(ROOT).parts):return False
    if p.name.endswith("-Index.md"):return False
    return True

def main():
    for lang in ("ES","EN"):
        base=ROOT/lang
        for p in sorted(base.rglob("*.md")):
            if not canonico(p):
                p.unlink()
                continue
            p.write_text(limpiar(p.read_text(encoding="utf-8")),encoding="utf-8")
        # limpia directorios vacíos
        for d in sorted((x for x in base.rglob("*") if x.is_dir()),reverse=True):
            try:d.rmdir()
            except OSError:pass
    return 0

if __name__=="__main__":raise SystemExit(main())
