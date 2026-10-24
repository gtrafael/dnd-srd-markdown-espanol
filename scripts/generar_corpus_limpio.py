#!/usr/bin/env python3
"""Genera in-place la variante limpia destinada a corpus.

Debe ejecutarse únicamente sobre una rama desechable creada desde main.
No corrige contenido normativo: elimina metadatos de Obsidian, índices y
duplicados estructurales ya identificados.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXCLUIR_ES: set[str] = set()
EXCLUIR_EN: set[str] = set()


def leer_frontmatter(texto: str) -> str:
    if not texto.startswith("---\n"):
        return ""
    fin = texto.find("\n---\n", 4)
    return texto[4:fin] if fin >= 0 else ""


def quitar_frontmatter(texto: str) -> str:
    if not texto.startswith("---\n"):
        return texto
    fin = texto.find("\n---\n", 4)
    return texto[fin + 5 :] if fin >= 0 else texto


def extraer_relaciones(frontmatter: str, campo: str) -> list[tuple[str, str]]:
    """Lee relaciones directas, a sección y uno-a-varios."""
    out: list[tuple[str, str]] = []

    for nombre in (campo, f"{campo}_section"):
        m = re.search(
            rf'^{re.escape(nombre)}:\s*"\[\[([^\]]+)\]\]"\s*$',
            frontmatter,
            flags=re.MULTILINE,
        )
        if m:
            out.append((nombre, m.group(1).split("|", 1)[0].strip()))

    plural = f"{campo}_sections"
    m = re.search(
        rf"^{re.escape(plural)}:\s*\[(.*?)\]\s*$",
        frontmatter,
        flags=re.MULTILINE,
    )
    if m:
        for destino in re.findall(r'"([^"]+)"', m.group(1)):
            out.append((plural, destino.strip()))

    return out


def limpiar_wikilinks(texto: str) -> str:
    def repl(m: re.Match[str]) -> str:
        contenido = m.group(1)
        if "|" in contenido:
            return contenido.rsplit("|", 1)[1]
        return contenido.rsplit("/", 1)[-1]

    return re.sub(r"\[\[([^\]]+)\]\]", repl, texto)


def limpiar(texto: str) -> str:
    texto = quitar_frontmatter(texto)
    texto = limpiar_wikilinks(texto)
    texto = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", texto)
    texto = re.sub(r"<img\b[^>]*>", "", texto, flags=re.IGNORECASE)
    texto = "\n".join(linea.rstrip() for linea in texto.splitlines())
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip() + "\n"


def excluir(rel: Path, idioma: str) -> bool:
    if any("(Alt)" in parte for parte in rel.parts):
        return True
    if rel.name in {"Espanol.md", "English.md"}:
        return True
    if rel.name.endswith("-Index.md"):
        return True
    tabla = EXCLUIR_ES if idioma == "ES" else EXCLUIR_EN
    return rel.as_posix() in tabla


def preparar_idioma(idioma: str, relaciones: list[dict]) -> None:
    raiz = ROOT / idioma
    campo = "related_en" if idioma == "ES" else "related_es"

    for directorio in sorted(
        (p for p in raiz.rglob("*") if p.is_dir() and "(Alt)" in p.name),
        reverse=True,
    ):
        shutil.rmtree(directorio)

    for path in sorted(raiz.rglob("*.md")):
        rel = path.relative_to(raiz)
        if excluir(rel, idioma):
            path.unlink()
            continue

        raw = path.read_text(encoding="utf-8")
        for campo_relacion, destino in extraer_relaciones(leer_frontmatter(raw), campo):
            relaciones.append(
                {
                    "idioma": idioma.lower(),
                    "archivo": rel.as_posix(),
                    "campo": campo_relacion,
                    "destino": destino,
                }
            )

        path.write_text(limpiar(raw), encoding="utf-8")

    for directorio in sorted((p for p in raiz.rglob("*") if p.is_dir()), reverse=True):
        if not any(directorio.iterdir()):
            directorio.rmdir()


def validar_salida(relaciones: list[dict]) -> None:
    """Comprueba la simetría mínima de la salida limpia ES/EN."""
    archivos = {}
    for idioma in ("ES", "EN"):
        raiz = ROOT / idioma
        docs = sorted(p.relative_to(raiz).as_posix() for p in raiz.rglob("*.md"))
        if any("(Alt)" in p or p.endswith("-Index.md") for p in docs):
            raise SystemExit(f"La salida {idioma} conserva índices auxiliares")
        archivos[idioma] = docs

    if len(archivos["ES"]) != len(archivos["EN"]):
        raise SystemExit(
            f"Corpus asimétrico: ES={len(archivos['ES'])}, EN={len(archivos['EN'])}"
        )

    relaciones_por_idioma = {
        idioma: sum(1 for r in relaciones if r["idioma"] == idioma.lower())
        for idioma in ("ES", "EN")
    }
    for idioma in ("ES", "EN"):
        if relaciones_por_idioma[idioma] != len(archivos[idioma]):
            raise SystemExit(
                f"Relaciones bilingües incompletas en {idioma}: "
                f"{relaciones_por_idioma[idioma]}/{len(archivos[idioma])}"
            )


def validar_recuadros_integrados() -> None:
    """Los recuadros son contenido del padre, nunca notas canónicas separadas."""
    separados = []
    for idioma in ("ES", "EN"):
        for path in (ROOT / idioma).rglob("*.md"):
            if "(Alt)" in path.as_posix() or path.name.endswith("-Index.md"):
                continue
            fm = leer_frontmatter(path.read_text(encoding="utf-8")).casefold()
            if "recuadro" in fm or "callout" in fm:
                separados.append(str(path.relative_to(ROOT)))
    if separados:
        raise SystemExit("Quedan recuadros separados: " + ", ".join(separados))

    esperados = {
        "ES/Clases/Mago.md": "### Ampliar y sustituir un libro de conjuros",
        "EN/Classes/Wizard.md": "### Expanding and Replacing a Spellbook",
        "ES/Conjuros/LanzarConjuros.md": "## Lanzar conjuros con armadura",
        "EN/Spells/Casting Spells.md": "## Casting in Armor",
        "ES/ComoJugar/Combate.md": "### Jugar con una cuadrícula",
        "EN/Playing the Game/Combat.md": "### Playing on a Grid",
    }
    for rel, heading in esperados.items():
        if heading not in (ROOT / rel).read_text(encoding="utf-8"):
            raise SystemExit(f"Falta recuadro integrado {heading!r} en {rel}")

def main() -> int:
    validar_recuadros_integrados()
    relaciones: list[dict] = []
    preparar_idioma("ES", relaciones)
    preparar_idioma("EN", relaciones)
    validar_salida(relaciones)

    metadata = ROOT / "metadata"
    metadata.mkdir(exist_ok=True)
    (metadata / "pares-bilingues.json").write_text(
        json.dumps({"relaciones": relaciones}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
