#!/usr/bin/env python3
"""Genera in-place la variante limpia destinada a custom/corpus.

Debe ejecutarse únicamente sobre una rama desechable creada desde custom/main.
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


def validar_fronteras_recuadros() -> None:
    combate = (ROOT / "ES/ComoJugar/Combate.md").read_text(encoding="utf-8")
    ocultos = (ROOT / "ES/ComoJugar/AtacantesYObjetivosOcultos.md").read_text(encoding="utf-8")

    frase = (
        "Intentar un ataque a distancia se complica si el enemigo está junto a ti. "
        "Cuando hagas un ataque a distancia, ya sea con un arma, un conjuro o cualquier "
        "otro medio, tendrás desventaja en la tirada si estás a 1,5 m o menos de un enemigo "
        "que pueda verte y no tenga el estado de incapacitado "
        "(consulta el capítulo “Glosario de reglas”)."
    )
    cola_espuria = "otro medio, tendrás desventaja en la tirada"

    if frase not in combate:
        raise SystemExit(
            "Regresión de frontera: la frase de ataques a distancia quedó truncada en Combate.md"
        )
    if cola_espuria in ocultos:
        raise SystemExit(
            "Regresión de frontera: AtacantesYObjetivosOcultos.md absorbió prosa de Combate.md"
        )

    lanzar = (ROOT / "ES/Conjuros/LanzarConjuros.md").read_text(encoding="utf-8")
    armadura = (ROOT / "ES/Conjuros/LanzarConjurosConArmadura.md").read_text(encoding="utf-8")
    casting = (ROOT / "EN/Spells/Casting Spells.md").read_text(encoding="utf-8")

    if "## Nivel del conjuro" not in lanzar or "## Listas de conjuros de clases" not in lanzar:
        raise SystemExit(
            "Regresión de frontera: LanzarConjuros.md perdió secciones anteriores al callout de armadura"
        )
    if "Nivel del conjuro" in armadura:
        raise SystemExit(
            "Regresión de frontera: LanzarConjurosConArmadura.md absorbió contenido del documento padre"
        )
    if "## Casting in Armour" in casting:
        raise SystemExit(
            "Regresión de frontera: Casting in Armor sigue duplicado dentro de Casting Spells.md"
        )


def main() -> int:
    relaciones: list[dict] = []
    preparar_idioma("ES", relaciones)
    preparar_idioma("EN", relaciones)
    validar_fronteras_recuadros()

    metadata = ROOT / "metadata"
    metadata.mkdir(exist_ok=True)
    (metadata / "pares-bilingues.json").write_text(
        json.dumps({"relaciones": relaciones}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
