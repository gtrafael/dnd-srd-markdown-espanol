#!/usr/bin/env python3
"""Migración única: alinea main con el TOC y reintegra los antiguos recuadros.

No debe ejecutarse de forma recurrente. Tras la migración, main es la fuente canónica.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text.rstrip() + "\n", encoding="utf-8")


def body(rel: str) -> str:
    text = read(rel)
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end >= 0:
            text = text[end + 5:]
    lines = text.lstrip().splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    return "\n".join(lines).strip()


def section(title: str, content: str, level: int = 2) -> str:
    return f"{'#' * level} {title}\n\n{content.strip()}"


def insert_before(parent: str, anchor: str, block: str) -> None:
    text = read(parent)
    if block.splitlines()[0] in text:
        return
    if anchor not in text:
        raise SystemExit(f"Anchor no encontrado en {parent}: {anchor}")
    write(parent, text.replace(anchor, block.rstrip() + "\n\n" + anchor, 1))


def append(parent: str, block: str) -> None:
    text = read(parent)
    if block.splitlines()[0] in text:
        return
    write(parent, text.rstrip() + "\n\n" + block.rstrip() + "\n")


def clean_callout(rel: str, title: str, parent: str, anchor: str | None, level: int) -> None:
    b = body(rel)
    block = section(title, b, level)
    if anchor:
        insert_before(parent, anchor, block)
    else:
        append(parent, block)
    (ROOT / rel).unlink()


def merge_spanish_specials() -> None:
    # El archivo aislado contenía, además del recuadro, secciones normales que
    # quedaron fuera del padre durante la extracción. Se reintegran juntas.
    b = body("ES/ComoJugar/Descansar.md")
    marker = "\n#### Daño contra varios objetivos"
    callout, regular = b.split(marker, 1)
    block = section("Descansar", callout, 3) + "\n\n### Daño contra varios objetivos" + regular
    insert_before("ES/ComoJugar/DanoYCuracion.md", "## Mitad del daño", block)
    (ROOT / "ES/ComoJugar/Descansar.md").unlink()

    b = body("ES/ComoJugar/InspiracionHeroica.md")
    marker = "\n### Clase de armadura"
    callout, regular = b.split(marker, 1)
    block = section("Inspiración heroica", callout, 3) + "\n\n### Clase de armadura" + regular
    insert_before("ES/ComoJugar/LasPruebasConD20.md", "## Ventaja y desventaja", block)
    (ROOT / "ES/ComoJugar/InspiracionHeroica.md").unlink()

    b = body("ES/ComoJugar/OrdenDeMarcha.md")
    marker = "\n### Peligros"
    callout, regular = b.split(marker, 1)
    block = section("Orden de marcha", callout, 2) + "\n\n### Peligros" + regular
    insert_before("ES/ComoJugar/Exploracion.md", "## Ritmo de viaje", block)
    (ROOT / "ES/ComoJugar/OrdenDeMarcha.md").unlink()

    b = body("ES/ComoJugar/RedondearHaciaAbajo.md")
    marker = "\n#### Modificadores por característica"
    callout, regular = b.split(marker, 1)
    block = section("Redondear hacia abajo", callout, 3) + "\n\n## Modificadores por característica" + regular
    append("ES/ComoJugar/LasCaracteristicas.md", block)
    (ROOT / "ES/ComoJugar/RedondearHaciaAbajo.md").unlink()

    # Jugar con cuadrícula: el archivo absorbió la continuación de "Tu turno".
    raw = body("ES/ComoJugar/JugarConUnaCuadricula.md")
    marker = "\naparece más adelante en “Cómo jugar”"
    if marker not in raw:
        raise SystemExit("No se reconoce la frontera de JugarConUnaCuadricula")
    callout, regular = raw.split(marker, 1)
    regular = ("aparece más adelante en “Cómo jugar”" + regular).replace(
        "#### Terminar el combate", "### Terminar el combate"
    )
    parent = read("ES/ComoJugar/Combate.md")
    needle = "El apartado “Movimiento y posición”, que\n\n## Movimiento y posición"
    if needle not in parent:
        raise SystemExit("No se reconoce la frontera de Tu turno en Combate.md")
    replacement = (
        "El apartado “Movimiento y posición”, que " + regular.strip()
        + "\n\n" + section("Jugar con una cuadrícula", callout, 3)
        + "\n\n## Movimiento y posición"
    )
    write("ES/ComoJugar/Combate.md", parent.replace(needle, replacement, 1))
    (ROOT / "ES/ComoJugar/JugarConUnaCuadricula.md").unlink()

    # Noquear: el archivo absorbió la continuación de muerte instantánea y dos secciones.
    raw = body("ES/ComoJugar/NoquearAUnaCriatura.md")
    marker = "\ngolpe máximos, pero ahora le quedan 6"
    if marker not in raw:
        raise SystemExit("No se reconoce la frontera de NoquearAUnaCriatura")
    callout, regular = raw.split(marker, 1)
    regular = ("golpe máximos, pero ahora le quedan 6" + regular).replace(
        "#### Caer inconsciente", "### Caer inconsciente"
    )
    parent = read("ES/ComoJugar/DanoYCuracion.md")
    needle = "Por ejemplo, si tu personaje tiene 12 puntos de\n\n## Tiradas de salvación contra muerte"
    if needle not in parent:
        raise SystemExit("No se reconoce la frontera de muerte instantánea")
    replacement = (
        "Por ejemplo, si tu personaje tiene 12 puntos de " + regular.strip()
        + "\n\n" + section("Noquear a una criatura", callout, 3)
        + "\n\n## Tiradas de salvación contra muerte"
    )
    write("ES/ComoJugar/DanoYCuracion.md", parent.replace(needle, replacement, 1))
    (ROOT / "ES/ComoJugar/NoquearAUnaCriatura.md").unlink()


def merge_callouts() -> None:
    merge_spanish_specials()

    es = [
        ("ES/ComoJugar/LasExcepcionesSeImponenALasReglasGenerales.md", "Las excepciones se imponen a las reglas generales", "ES/ComoJugar/ElRitmoDeJuego.md", None, 2),
        ("ES/ComoJugar/AtacantesYObjetivosOcultos.md", "Atacantes y objetivos ocultos", "ES/ComoJugar/Combate.md", "#### Ataques a distancia", 4),
        ("ES/CreacionDePersonajes/CriaturasSinAlineamiento.md", "Criaturas sin alineamiento", "ES/CreacionDePersonajes/CrearTuPersonaje.md", "### Paso 5: detalles de la creación del personaje", 3),
        ("ES/CreacionDePersonajes/DotesAdicionalesEnNivel20.md", "Dotes adicionales en el nivel 20", "ES/CreacionDePersonajes/ProgresionDeNiveles.md", None, 3),
        ("ES/Clases/AmpliarYSustituirUnLibroDeConjuros.md", "Ampliar y sustituir un libro de conjuros", "ES/Clases/Mago.md", "### Nivel 1: Adepto en rituales", 3),
        ("ES/Clases/RomperTuJuramento.md", "Romper tu juramento", "ES/Clases/Paladin.md", "### Nivel 3: Canalizar divinidad", 4),
        ("ES/Equipo/ArmasImprovisadas.md", "Armas improvisadas", "ES/Equipo/Armas.md", "## Competencia con armas", 2),
        ("ES/Equipo/VenderEquipo.md", "Vender equipo", "ES/Equipo/Armas.md", "## Competencia con armas", 2),
        ("ES/Conjuros/IdentificarUnConjuroActivo.md", "Identificar un conjuro activo", "ES/Conjuros/LanzarConjuros.md", "## Tiradas de salvación", 3),
        ("ES/Conjuros/LanzarConjurosConArmadura.md", "Lanzar conjuros con armadura", "ES/Conjuros/LanzarConjuros.md", "## Nivel del conjuro", 2),
        ("ES/ObjetosMagicos/ReglasDeObjetosMagicos.md", "Reglas de objetos mágicos", "ES/ObjetosMagicos/ObjetosMagicos.md", None, 2),
    ]
    for args in es:
        clean_callout(*args)

    en = [
        ("EN/Playing the Game/Exceptions Supersede General Rules.md", "Exceptions Supersede General Rules", "EN/Playing the Game/Rhythm of Play.md", None, 2),
        ("EN/Playing the Game/Round Down.md", "Round Down", "EN/Playing the Game/The Six Abilities.md", "## Ability Modifiers", 3),
        ("EN/Playing the Game/Heroic Inspiration.md", "Heroic Inspiration", "EN/Playing the Game/D20 Tests.md", "### Armour Class", 3),
        ("EN/Playing the Game/Marching Order.md", "Marching Order", "EN/Playing the Game/Exploration.md", "## Hazards", 2),
        ("EN/Playing the Game/Playing on a Grid.md", "Playing on a Grid", "EN/Playing the Game/Combat.md", "## Movement and Position", 3),
        ("EN/Playing the Game/Unseen Attackers and Targets.md", "Unseen Attackers and Targets", "EN/Playing the Game/Combat.md", "## Ranged Attacks", 3),
        ("EN/Playing the Game/Resting.md", "Resting", "EN/Playing the Game/Damage and Healing.md", "### Damage against Multiple Targets", 3),
        ("EN/Playing the Game/Knocking Out a Creature.md", "Knocking Out a Creature", "EN/Playing the Game/Damage and Healing.md", "### Death Saving Throws", 3),
        ("EN/Character Creation/Unaligned Creatures.md", "Unaligned Creatures", "EN/Character Creation/Create Your Character.md", "## Step 5: Character Creation Details", 3),
        ("EN/Character Creation/Bonus Feats at Level 20.md", "Bonus Feats at Level 20", "EN/Character Creation/Level Advancement.md", None, 3),
        ("EN/Classes/Expanding and Replacing a Spellbook.md", "Expanding and Replacing a Spellbook", "EN/Classes/Wizard.md", "### Level 1: Ritual Adept", 3),
        ("EN/Classes/Breaking Your Oath.md", "Breaking Your Oath", "EN/Classes/Paladin.md", "### Level 3: Channel Divinity", 4),
        ("EN/Equipment/Improvised Weapons.md", "Improvised Weapons", "EN/Equipment/Weapons.md", "## Weapon Proficiency", 2),
        ("EN/Equipment/Selling Equipment.md", "Selling Equipment", "EN/Equipment/Weapons.md", "## Weapon Proficiency", 2),
        ("EN/Spells/Identifying an Ongoing Spell.md", "Identifying an Ongoing Spell", "EN/Spells/Casting Spells.md", "## Saving Throws", 3),
        ("EN/Spells/Casting in Armor.md", "Casting in Armor", "EN/Spells/Casting Spells.md", "## Spell Level", 2),
        ("EN/Magic Items/Magic Item Rules.md", "Magic Item Rules", "EN/Magic Items/Magic Items.md", None, 2),
    ]
    for args in en:
        clean_callout(*args)


def move_catalog(root_rel: str, dst_name: str, keep: set[str]) -> list[tuple[str, str]]:
    root = ROOT / root_rel
    dst = root / dst_name
    dst.mkdir(exist_ok=True)
    moved: list[tuple[str, str]] = []
    for p in list(root.glob("*.md")):
        if p.name in keep or p.name.endswith("-Index.md") or p.name.startswith("00-"):
            continue
        target = dst / p.name
        p.rename(target)
        moved.append((p.stem, target.relative_to(ROOT / root_rel.split("/", 1)[0]).with_suffix("").as_posix()))
    return moved


def replace_links(moves: list[tuple[str, str]], old_prefix: str, lang: str) -> None:
    lang_root = ROOT / lang
    for p in lang_root.rglob("*.md"):
        text = p.read_text(encoding="utf-8")
        new = text
        for stem, new_target in moves:
            new = new.replace(f"[[{old_prefix}/{stem}|", f"[[{new_target}|")
            new = new.replace(f"[[{old_prefix}/{stem}]]", f"[[{new_target}]]")
        if new != text:
            p.write_text(new, encoding="utf-8")


def move_catalogs() -> None:
    es_spells = move_catalog(
        "ES/Conjuros", "DescripcionesDeConjuros",
        {"Conjuros.md", "ObtenerConjuros.md", "LanzarConjuros.md"},
    )
    en_spells = move_catalog(
        "EN/Spells", "Spell Descriptions",
        {"Spells.md", "Gaining Spells.md", "Casting Spells.md"},
    )
    es_items = move_catalog(
        "ES/ObjetosMagicos", "ObjetosMagicosDeLaAALaZ",
        {
            "ObjetosMagicos.md", "CategoriasDeObjetosMagicos.md", "RarezaDeLosObjetosMagicos.md",
            "ActivarUnObjetoMagico.md", "ElSiguienteAmanecer.md", "ObjetosMalditos.md",
            "ResistenciaDeLosObjetosMagicos.md", "FabricarObjetosMagicos.md",
            "ObjetosMagicosConscientes.md",
        },
    )
    en_items = move_catalog(
        "EN/Magic Items", "Magic Items A-Z",
        {
            "Magic Items.md", "Magic Item Categories.md", "Magic Item Rarity.md",
            "Activating a Magic Item.md", "The Next Dawn.md", "Cursed Items.md",
            "Magic Item Resilience.md", "Crafting Magic Items.md", "Sentient Magic Items.md",
        },
    )

    replace_links(es_spells, "Conjuros", "ES")
    replace_links(en_spells, "Spells", "EN")
    replace_links(es_items, "ObjetosMagicos", "ES")
    replace_links(en_items, "Magic Items", "EN")

    # Las relaciones cruzadas viven en el idioma opuesto.
    replace_links(en_spells, "Spells", "ES")
    replace_links(es_spells, "Conjuros", "EN")
    replace_links(en_items, "Magic Items", "ES")
    replace_links(es_items, "ObjetosMagicos", "EN")


def replace_callout_links() -> None:
    replacements = [
        ("[[ComoJugar/LasExcepcionesSeImponenALasReglasGenerales", "[[ComoJugar/ElRitmoDeJuego#Las excepciones se imponen a las reglas generales"),
        ("[[Playing the Game/Exceptions Supersede General Rules", "[[Playing the Game/Rhythm of Play#Exceptions Supersede General Rules"),
        ("[[ComoJugar/RedondearHaciaAbajo", "[[ComoJugar/LasCaracteristicas#Redondear hacia abajo"),
        ("[[Playing the Game/Round Down", "[[Playing the Game/The Six Abilities#Round Down"),
        ("[[ComoJugar/InspiracionHeroica", "[[ComoJugar/LasPruebasConD20#Inspiración heroica"),
        ("[[Playing the Game/Heroic Inspiration", "[[Playing the Game/D20 Tests#Heroic Inspiration"),
        ("[[ComoJugar/OrdenDeMarcha", "[[ComoJugar/Exploracion#Orden de marcha"),
        ("[[Playing the Game/Marching Order", "[[Playing the Game/Exploration#Marching Order"),
        ("[[ComoJugar/JugarConUnaCuadricula", "[[ComoJugar/Combate#Jugar con una cuadrícula"),
        ("[[Playing the Game/Playing on a Grid", "[[Playing the Game/Combat#Playing on a Grid"),
        ("[[ComoJugar/AtacantesYObjetivosOcultos", "[[ComoJugar/Combate#Atacantes y objetivos ocultos"),
        ("[[Playing the Game/Unseen Attackers and Targets", "[[Playing the Game/Combat#Unseen Attackers and Targets"),
        ("[[ComoJugar/Descansar", "[[ComoJugar/DanoYCuracion#Descansar"),
        ("[[Playing the Game/Resting", "[[Playing the Game/Damage and Healing#Resting"),
        ("[[ComoJugar/NoquearAUnaCriatura", "[[ComoJugar/DanoYCuracion#Noquear a una criatura"),
        ("[[Playing the Game/Knocking Out a Creature", "[[Playing the Game/Damage and Healing#Knocking Out a Creature"),
        ("[[CreacionDePersonajes/CriaturasSinAlineamiento", "[[CreacionDePersonajes/CrearTuPersonaje#Criaturas sin alineamiento"),
        ("[[Character Creation/Unaligned Creatures", "[[Character Creation/Create Your Character#Unaligned Creatures"),
        ("[[CreacionDePersonajes/DotesAdicionalesEnNivel20", "[[CreacionDePersonajes/ProgresionDeNiveles#Dotes adicionales en el nivel 20"),
        ("[[Character Creation/Bonus Feats at Level 20", "[[Character Creation/Level Advancement#Bonus Feats at Level 20"),
        ("[[Clases/AmpliarYSustituirUnLibroDeConjuros", "[[Clases/Mago#Ampliar y sustituir un libro de conjuros"),
        ("[[Classes/Expanding and Replacing a Spellbook", "[[Classes/Wizard#Expanding and Replacing a Spellbook"),
        ("[[Clases/RomperTuJuramento", "[[Clases/Paladin#Romper tu juramento"),
        ("[[Classes/Breaking Your Oath", "[[Classes/Paladin#Breaking Your Oath"),
        ("[[Equipo/ArmasImprovisadas", "[[Equipo/Armas#Armas improvisadas"),
        ("[[Equipment/Improvised Weapons", "[[Equipment/Weapons#Improvised Weapons"),
        ("[[Equipo/VenderEquipo", "[[Equipo/Armas#Vender equipo"),
        ("[[Equipment/Selling Equipment", "[[Equipment/Weapons#Selling Equipment"),
        ("[[Conjuros/IdentificarUnConjuroActivo", "[[Conjuros/LanzarConjuros#Identificar un conjuro activo"),
        ("[[Spells/Identifying an Ongoing Spell", "[[Spells/Casting Spells#Identifying an Ongoing Spell"),
        ("[[Conjuros/LanzarConjurosConArmadura", "[[Conjuros/LanzarConjuros#Lanzar conjuros con armadura"),
        ("[[Spells/Casting in Armor", "[[Spells/Casting Spells#Casting in Armor"),
        ("[[ObjetosMagicos/ReglasDeObjetosMagicos", "[[ObjetosMagicos/ObjetosMagicos#Reglas de objetos mágicos"),
        ("[[Magic Items/Magic Item Rules", "[[Magic Items/Magic Items#Magic Item Rules"),
    ]
    for lang in ("ES", "EN"):
        for p in (ROOT / lang).rglob("*.md"):
            text = p.read_text(encoding="utf-8")
            new = text
            for old, newv in replacements:
                new = new.replace(old, newv)
            if new != text:
                p.write_text(new, encoding="utf-8")


def main() -> int:
    merge_callouts()
    replace_callout_links()
    move_catalogs()
    print("Estructura canónica migrada al TOC y recuadros reintegrados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
