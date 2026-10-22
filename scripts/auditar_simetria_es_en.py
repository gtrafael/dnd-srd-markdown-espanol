#!/usr/bin/env python3
"""Comprueba que ES, referencia canónica, tenga un espejo EN válido."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path


EXCLUIR_ES = {
    "GlosarioDeReglas/DefinicionesDeLasReglas.md",
}


def frontmatter(texto: str) -> str:
    if not texto.startswith("---\n"):
        return ""
    fin = texto.find("\n---\n", 4)
    return texto[4:fin] if fin >= 0 else ""


def norm(texto: str) -> str:
    s = unicodedata.normalize("NFKD", texto)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[*_]+", "", s)
    return re.sub(r"\s+", " ", s.casefold()).strip()


def wikilink(fm: str, campo: str) -> str | None:
    m = re.search(rf'^{re.escape(campo)}:\s*"\[\[([^\]]+)\]\]"\s*$', fm, re.MULTILINE)
    return m.group(1).split("|", 1)[0].strip() if m else None


def relaciones_en(fm: str) -> list[tuple[str, str]]:
    out = []
    for campo in ("related_en", "related_en_section"):
        destino = wikilink(fm, campo)
        if destino:
            out.append((campo, destino))
    m = re.search(r"^related_en_sections:\s*\[(.*?)\]\s*$", fm, re.MULTILINE)
    if m:
        out.extend(("related_en_sections", x) for x in re.findall(r'"([^"]+)"', m.group(1)))
    return out


def headings(path: Path) -> set[str]:
    return {
        norm(m.group(1))
        for linea in path.read_text(encoding="utf-8").splitlines()
        if (m := re.match(r"^#{1,6}\s+(.+?)\s*$", linea))
    }


def audit(es_root: Path, en_root: Path) -> dict:
    fallos = []
    revisados = 0
    relaciones = 0

    for path in sorted(es_root.rglob("*.md")):
        rel = path.relative_to(es_root)
        if any("(Alt)" in p for p in rel.parts):
            continue
        if rel.name == "Espanol.md" or rel.name.endswith("-Index.md") or rel.as_posix() in EXCLUIR_ES:
            continue

        revisados += 1
        raw = path.read_text(encoding="utf-8")
        fm = frontmatter(raw)
        pares = relaciones_en(fm)
        sin_equivalente = "sin-equivalente" in fm

        if not pares:
            fallos.append({"tipo": "sin_relacion_en", "archivo": rel.as_posix()})
            continue
        if sin_equivalente:
            fallos.append({"tipo": "etiqueta_sin_equivalente_obsoleta", "archivo": rel.as_posix()})

        modo = re.search(r'^alignment_mode:\s*"?([^"\n]+)"?\s*$', fm, re.MULTILINE)
        modo = modo.group(1).strip() if modo else "file"

        for campo, destino in pares:
            relaciones += 1
            ruta, _, seccion = destino.partition("#")
            en_path = en_root / f"{ruta}.md"
            if not en_path.exists():
                fallos.append({
                    "tipo": "destino_en_inexistente",
                    "archivo": rel.as_posix(),
                    "destino": destino,
                })
                continue

            if seccion and norm(seccion) not in headings(en_path):
                fallos.append({
                    "tipo": "seccion_en_inexistente",
                    "archivo": rel.as_posix(),
                    "destino": destino,
                })

            if campo == "related_en" and modo == "file":
                en_fm = frontmatter(en_path.read_text(encoding="utf-8"))
                vuelta = wikilink(en_fm, "related_es")
                esperado = rel.with_suffix("").as_posix()
                if vuelta != esperado:
                    fallos.append({
                        "tipo": "relacion_no_reciproca",
                        "archivo": rel.as_posix(),
                        "destino": destino,
                        "related_es": vuelta,
                    })

    return {
        "summary": {
            "archivos_es_revisados": revisados,
            "relaciones_es_en": relaciones,
            "fallos": len(fallos),
        },
        "fallos": fallos,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--es", type=Path, default=Path("ES"))
    ap.add_argument("--en", type=Path, default=Path("EN"))
    ap.add_argument("--salida", type=Path, default=Path("auditoria-simetria.json"))
    args = ap.parse_args()

    out = audit(args.es, args.en)
    args.salida.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out["summary"], ensure_ascii=False))
    for fallo in out["fallos"][:100]:
        print(json.dumps(fallo, ensure_ascii=False))
    return 1 if out["fallos"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
