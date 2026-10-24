#!/usr/bin/env python3
"""Aplica a main correcciones mecánicas ya verificadas contra el SRD oficial.

Conserva frontmatter, aliases, tags y wikilinks de Obsidian.
No decide jerarquía, no mueve secciones y no reconstruye tablas a partir del PDF.
La jerarquía se valida contra el TOC oficial mediante los gates del repositorio.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1] / "ES"

CORRECCIONES_LITERAL = {
    "Destra-barse": "Destrabarse",
    "Escon-derse": "Esconderse",
    "desven-taja": "desventaja",
    "Explora-dor": "Explorador",
    "Superviven-cia": "Supervivencia",
    "Hechi-cero": "Hechicero",
    "legiona-rio": "legionario",
    "Lan-zamiento": "Lanzamiento",
    "ma-lla": "malla",
    "esporá-dicamente": "esporádicamente",
    "Gargan-tuesco": "Gargantuesco",
    "caó-tico": "caótico",
    "de-seo": "deseo",
    "con-ceda": "conceda",
    "da-ñar": "dañar",
    "empu-ñando": "empuñando",
    "tama-ño": "tamaño",
    "Du-rante": "Durante",
    "constre-ñir": "constreñir",
    "Constitucionalfinalde cadahoraosumará1nivel": "Constitución al final de cada hora o sumará 1 nivel",
    "beberlaoadministrarlaaotra": "beberla o administrarla a otra",
    "conjurorestablecimiento": "conjuro restablecimiento",
    "deConstitución": "de Constitución",
    "deaventuras": "de aventuras",
    "deunmismo": "de un mismo",
    "durante1minuto": "durante 1 minuto",
    "en élo si está": "en él o si está",
    "en3": "en 3",
    "estadode": "estado de",
    "fallao": "falla o",
    "infernala": "infernal a",
    "lafalla": "la falla",
    "moverá3": "moverá 3",
    "notienen": "no tienen",
    "petrificadohasta": "petrificado hasta",
    "sufrirála": "sufrirá la",
    "superaruna": "superar una",
    "versobre": "ver sobre",
    "6d1o": "6d10",
    "3 myluz": "3 m y luz",
    "mas alla": "más allá",
    "\\frac{1}{2}": "½",
    "\\times": "×",
    "Sila criatura": "Si la criatura",
}

CORRECCIONES_PALABRA = {
    "accion": "acción",
    "ademas": "además",
    "automaticamente": "automáticamente",
    "caracteristica": "característica",
    "condicion": "condición",
    "constitucion": "constitución",
    "dano": "daño",
    "demas": "demás",
    "dias": "días",
    "dificil": "difícil",
    "eleccion": "elección",
    "haran": "harán",
    "informacion": "información",
    "linea": "línea",
    "numero": "número",
    "pequeno": "pequeño",
    "podras": "podrás",
    "podrias": "podrías",
    "sabiduria": "sabiduría",
    "salvacion": "salvación",
    "tamano": "tamaño",
    "tendras": "tendrás",
    "maximo": "máximo",
    "tendra": "tendrá",
    "continuacion": "continuación",
    "tendran": "tendrán",
    "delconjuro": "del conjuro",
    "maestria": "maestría",
    "dela": "de la",
    "deberan": "deberán",
    "sabiduriao": "Sabiduría o",
    "campanaes": "campaña es",
    "terminara": "terminará",
    "lineas": "líneas",
    "funcion": "función",
    "interactuas": "interactúas",
    "tablaa": "tabla a",
    "demoniaco": "demoníaco",
    "haceruna": "hacer una",
    "emanacion": "emanación",
    "estara": "estará",
    "paladin": "paladín",
    "estaras": "estarás",
    "banará": "bañará",
    "acierteauna": "acierte a una",
    "criaturaafectada": "criatura afectada",
    "salvea": "salve a",
    "tuamor": "tu amor",
    "circulos": "círculos",
    "muestraa": "muestra a",
    "puedenatravesarla": "pueden atravesarla",
    "vuelvesa": "vuelves a",
    "sufriran": "sufrirán",
    "vision": "visión",
    "derelámpago": "de relámpago",
    "sisupera": "Si supera",
    "cuentade": "cuenta de",
    "unmismo": "un mismo",
    "desabiduría": "de Sabiduría",
    "lasupera": "la supera",
    "estadoterminará": "estado terminará",
    "otroplano": "otro plano",
    "dosveces": "dos veces",
    "destrezao": "Destreza o",
    "movera": "moverá",
    "sufrirá12d6": "sufrirá 12d6",
    "empezaranaarder": "empezarán a arder",
    "armasa": "armas a",
    "detallaa": "detalla a",
    "aceiteardera": "aceite arderá",
    "siaciertas": "Si aciertas",
    "estaarma": "esta arma",
    "caeran": "caerán",
    "maldicion": "maldición",
    "infectara": "infectará",
    "referenciaaellas": "referencia a ellas",
    "anotacion": "anotación",
    "paraun": "para un",
    "frio": "frío",
    "empunes": "empuñes",
    "descritasa": "descritas a",
    "repetirála": "repetirá la",
    "salvacional": "salvación al",
    "alaire": "al aire",
    "activacion": "activación",
    "ylas": "y las",
    "determinaal": "determina al",
    "detector": "detectar",
}

def reemplazar_palabra(texto: str, origen: str, destino: str) -> str:
    def repl(m: re.Match[str]) -> str:
        original = m.group(0)
        return destino[:1].upper() + destino[1:] if original[:1].isupper() else destino
    return re.sub(rf"\b{re.escape(origen)}\b", repl, texto, flags=re.IGNORECASE)

def normalizar(texto: str) -> str:
    """Normaliza solo el cuerpo; el frontmatter contiene rutas e identificadores."""
    cabecera = ""
    cuerpo = texto
    if texto.startswith("---\n"):
        fin = texto.find("\n---\n", 4)
        if fin >= 0:
            cabecera = texto[: fin + 5]
            cuerpo = texto[fin + 5 :]

    cuerpo = unicodedata.normalize("NFC", cuerpo)
    cuerpo = cuerpo.replace("\u00ad", "").replace("\u00a0", " ").replace("ä", "á")

    for origen, destino in CORRECCIONES_LITERAL.items():
        cuerpo = cuerpo.replace(origen, destino)
    for origen, destino in CORRECCIONES_PALABRA.items():
        cuerpo = reemplazar_palabra(cuerpo, origen, destino)

    cuerpo = re.sub(r"([\.,;:!?])(?=[A-Za-zÁÉÍÓÚÜÑáéíóúüñ])", r"\1 ", cuerpo)
    cuerpo = re.sub(r"\bCD(?=\d)", "CD ", cuerpo)
    cuerpo = re.sub(
        r"(?<=[A-Za-zÁÉÍÓÚÜÑáéíóúüñ,])\n\n(?=[a-záéíóúüñ])",
        " ",
        cuerpo,
    )
    cuerpo = cuerpo.replace(
        "| Stats | Valor | Mod | Salv |",
        "| Característica | Puntuación | Mod. | Salv. |",
    )
    cuerpo = "\n".join(line.rstrip() for line in cuerpo.splitlines()).rstrip() + "\n"
    return cabecera + cuerpo

def es_canonico(path: Path) -> bool:
    rel = path.relative_to(RAIZ)
    if any("(Alt)" in p for p in rel.parts):
        return False
    return path.name != "Espanol.md" and not path.name.endswith("-Index.md")

def main() -> int:
    cambios = []
    for path in sorted(RAIZ.rglob("*.md")):
        if not es_canonico(path):
            continue
        original = path.read_text(encoding="utf-8")
        nuevo = normalizar(original)
        if nuevo != original:
            path.write_text(nuevo, encoding="utf-8")
            cambios.append(str(path.relative_to(RAIZ.parent)))

    print(f"Archivos modificados: {len(cambios)}")
    for path in cambios:
        print(path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
