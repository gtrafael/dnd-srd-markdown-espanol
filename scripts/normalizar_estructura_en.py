#!/usr/bin/env python3
"""Normaliza la estructura inglesa según el TOC oficial del SRD 5.2.1.

Es una migración idempotente y segura para reejecuciones. La estructura documental la decide el índice
oficial; los callouts y las notas hoja de catálogos se conservan como
excepciones explícitas.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EN = ROOT / "EN"
ES = ROOT / "ES"


def strip_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    return text[end + 5:] if end >= 0 else text


def frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---\n", 4)
    return text[:end + 5] if end >= 0 else ""


def section(text: str, start: str, end: str | None = None) -> str:
    body = strip_frontmatter(text)

    def locate(heading: str, offset: int = 0) -> int:
        pattern = re.compile(rf"(?m)^{re.escape(heading)}\s*$")
        m = pattern.search(body, offset)
        return m.start() if m else -1

    a = locate(start)
    if a < 0:
        raise ValueError(f"No se encuentra el encabezado exacto {start!r}")
    b = locate(end, a + len(start)) if end else -1
    return (body[a:b] if b >= 0 else body[a:]).strip() + "\n"


def demote(text: str, levels: int = 1) -> str:
    def repl(m: re.Match[str]) -> str:
        return "#" * (len(m.group(1)) + levels) + m.group(2)
    return re.sub(r"^(#{1,5})(\s+)", repl, text, flags=re.MULTILINE)


def promote(text: str, levels: int = 1) -> str:
    def repl(m: re.Match[str]) -> str:
        return "#" * max(1, len(m.group(1)) - levels) + m.group(2)
    return re.sub(r"^(#{2,6})(\s+)", repl, text, flags=re.MULTILINE)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def move(src: Path, dst: Path) -> None:
    if dst.exists():
        if src.exists():
            src.unlink()
        return
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)


def note(title: str, aliases: list[str], tag: str, body: str, relation: str = "") -> str:
    alias_text = ", ".join(f'"{x}"' for x in aliases)
    rel = relation + "\n" if relation else ""
    return (
        "---\n"
        f"aliases: [{alias_text}]\n"
        f"tags: [srd, english, {tag}]\n"
        f"{rel}"
        "---\n\n"
        f"{body.strip()}\n"
    )


def replace_all(root: Path, replacements: list[tuple[str, str]]) -> None:
    for p in root.rglob("*.md"):
        old = p.read_text(encoding="utf-8")
        new = old
        for a, b in replacements:
            new = new.replace(a, b)
        if new != old:
            p.write_text(new, encoding="utf-8")


def playing_the_game() -> None:
    src = EN / "Gameplay"
    dst = EN / "Playing the Game"
    dst.mkdir(exist_ok=True)

    abilities = src / "Abilities.md"
    if abilities.exists():
        raw = abilities.read_text(encoding="utf-8")
        specs = [
            ("# The Six Abilities", "# D20 Tests", "The Six Abilities.md", "The Six Abilities",
             'related_es: "[[ComoJugar/LasCaracteristicas|Las características (Español)]]"'),
            ("# D20 Tests", "# Advantage/Disadvantage", "D20 Tests.md", "D20 Tests",
             'related_es: "[[ComoJugar/LasPruebasConD20|Las pruebas con d20 (Español)]]"'),
            ("# Advantage/Disadvantage", "# Proficiency", "Advantage-Disadvantage.md", "Advantage/Disadvantage",
             'related_es_section: "[[ComoJugar/LasPruebasConD20#Ventaja y desventaja|Ventaja y desventaja (Español)]]"\nalignment_mode: "section"'),
            ("# Proficiency", None, "Proficiency.md", "Proficiency",
             'related_es: "[[ComoJugar/Competencia|Competencia (Español)]]"'),
        ]
        for start, end, filename, title, rel in specs:
            body = section(raw, start, end)
            write(dst / filename, note(title, [title], "tag_gameplay", body, rel))
        abilities.unlink()

    adv = src / "Adventuring.md"
    if adv.exists():
        raw = adv.read_text(encoding="utf-8")
        for start, end, filename, title, rel in [
            ("# Social Interaction", "# Exploration", "Social Interaction.md", "Social Interaction",
             'related_es: "[[ComoJugar/InteraccionesSociales|Interacciones sociales (Español)]]"'),
            ("# Exploration", None, "Exploration.md", "Exploration",
             'related_es: "[[ComoJugar/Exploracion|Exploración (Español)]]"'),
        ]:
            body = section(raw, start, end)
            write(dst / filename, note(title, [title], "tag_gameplay", body, rel))
        adv.unlink()

    combat = src / "Combat.md"
    if combat.exists():
        raw = combat.read_text(encoding="utf-8")
        actions = section(raw, "# Actions", "# Combat")
        actions = actions.replace("\n# Bonus Actions", "\n## Bonus Actions").replace("\n# Reactions", "\n## Reactions")
        write(dst / "Actions.md", note(
            "Actions", ["Actions"], "tag_gameplay", actions,
            'related_es: "[[ComoJugar/Acciones|Acciones (Español)]]"'
        ))
        for start, end, filename, title, rel in [
            ("# Combat", "# Damage and Healing", "Combat.md", "Combat",
             'related_es: "[[ComoJugar/Combate|Combate (Español)]]"'),
            ("# Damage and Healing", None, "Damage and Healing.md", "Damage and Healing",
             'related_es: "[[ComoJugar/DanoYCuracion|Daño y curación (Español)]]"'),
        ]:
            body = section(raw, start, end)
            write(dst / filename, note(title, [title], "tag_gameplay", body, rel))
        combat.unlink()

    for p in list(src.glob("*.md")):
        if p.name == "Gameplay.md":
            p.unlink()
            continue
        move(p, dst / p.name)

    write(dst / "Playing the Game-Index.md", """# Playing the Game

- [[Rhythm of Play]]
- [[The Six Abilities]]
- [[D20 Tests]]
- [[Proficiency]]
- [[Actions]]
- [[Social Interaction]]
- [[Exploration]]
- [[Combat]]
- [[Damage and Healing]]
""")
    if src.exists() and not any(src.iterdir()):
        src.rmdir()


def character_origins_and_feats() -> None:
    origins = EN / "Character Origins"
    origins.mkdir(exist_ok=True)

    backgrounds = EN / "Characterizations" / "Backgrounds.md"
    if backgrounds.exists():
        raw = backgrounds.read_text(encoding="utf-8")
        body = strip_frontmatter(raw).replace("# Backgrounds", "# Character Backgrounds", 1)
        write(origins / "Character Backgrounds.md", note(
            "Character Backgrounds", ["Character Backgrounds", "Backgrounds"], "tag_character_origins", body,
            'related_es: "[[OrigenesDePersonaje/TrasfondosDePersonaje|Trasfondos de personaje (Español)]]"'
        ))
        backgrounds.unlink()

    species_dir = EN / "Species"
    species = species_dir / "Species.md"
    if species.exists():
        raw = species.read_text(encoding="utf-8")
        write(origins / "Character Species.md", note(
            "Character Species", ["Character Species", "Species"], "tag_character_origins",
            strip_frontmatter(raw),
            'related_es: "[[OrigenesDePersonaje/EspeciesDePersonaje|Especies de personaje (Español)]]"'
        ))
        species.unlink()
    if species_dir.exists():
        for p in list(species_dir.glob("*.md")):
            if p.name == "Species-Index.md":
                p.unlink()
            else:
                move(p, origins / p.name)
        if not any(species_dir.iterdir()):
            species_dir.rmdir()

    species_names = sorted(
        p.stem for p in origins.glob("*.md")
        if p.name not in {"Character Backgrounds.md", "Character Species.md", "Character Origins-Index.md"}
    )
    idx = ["# Character Origins", "", "- [[Character Backgrounds]]", "- [[Character Species]]", ""]
    idx += [f"- [[{x}]]" for x in species_names]
    write(origins / "Character Origins-Index.md", "\n".join(idx))

    feat_src = EN / "Characterizations" / "Feats.md"
    feats = EN / "Feats"
    feats.mkdir(exist_ok=True)
    if feat_src.exists():
        raw = feat_src.read_text(encoding="utf-8")
        body = strip_frontmatter(raw)
        body = re.sub(r"^# Feats\s*\n+", "", body)
        body = body.replace("## Feat Descriptions", "# Feat Descriptions", 1)
        write(feats / "Feat Descriptions.md", note(
            "Feat Descriptions", ["Feat Descriptions", "Feats"], "tag_feats", body,
            'related_es: "[[Dotes/DescripcionesDeDotes|Descripciones de dotes (Español)]]"'
        ))
        feat_src.unlink()

    feat_doc = feats / "Feat Descriptions.md"
    if feat_doc.exists():
        raw = feat_doc.read_text(encoding="utf-8")
        body = strip_frontmatter(raw)
        specs = [
            ("## Origin Feats", "## General Feats", "Origin Feats.md", "Origin Feats",
             'related_es: "[[Dotes/DotesDeOrigen|Dotes de origen (Español)]]"'),
            ("## General Feats", "## Fighting Style Feats", "General Feats.md", "General Feats",
             'related_es: "[[Dotes/DotesGenerales|Dotes generales (Español)]]"'),
            ("## Fighting Style Feats", "## Epic Boon Feats", "Fighting Style Feats.md", "Fighting Style Feats",
             'related_es: "[[Dotes/DotesDeEstiloDeCombate|Dotes de estilo de combate (Español)]]"'),
            ("## Epic Boon Feats", None, "Epic Boon Feats.md", "Epic Boon Feats",
             'related_es: "[[Dotes/DotesDeDonEpico|Dotes de don épico (Español)]]"'),
        ]
        if all(start in body for start, *_ in specs):
            intro = body.split("\n## Origin Feats", 1)[0].rstrip() + "\n"
            write(feat_doc, note(
                "Feat Descriptions", ["Feat Descriptions", "Feats"], "tag_feats", intro,
                'related_es: "[[Dotes/DescripcionesDeDotes|Descripciones de dotes (Español)]]"'
            ))
            for start, end, filename, title, rel in specs:
                part = promote(section(raw, start, end))
                write(feats / filename, note(title, [title], "tag_feats", part, rel))

    write(feats / "Feats-Index.md", """# Feats

- [[Feat Descriptions]]
- [[Origin Feats]]
- [[General Feats]]
- [[Fighting Style Feats]]
- [[Epic Boon Feats]]
""")

    chars = EN / "Characterizations"
    if chars.exists():
        for p in list(chars.glob("*.md")):
            p.unlink()
        if not any(chars.iterdir()):
            chars.rmdir()


def equipment() -> None:
    root = EN / "Equipment"
    move(root / "Coinage.md", root / "Coins.md")
    move(root / "Gear.md", root / "Adventuring Gear.md")
    move(root / "Transportation.md", root / "Mounts and Vehicles.md")

    weapons = root / "Weapons.md"
    props = root / "Properties.md"
    mastery = root / "Mastery Properties.md"
    if weapons.exists():
        w = weapons.read_text(encoding="utf-8")
        body = strip_frontmatter(w)
        if all(x in body for x in ("## Properties", "## Mastery Properties", "## Weapons Table")):
            p = promote(section(w, "## Properties", "## Mastery Properties"))
            m = promote(section(w, "## Mastery Properties", "## Weapons Table"))
            write(props, note(
                "Properties", ["Properties"], "tag_equipment", p,
                'related_es: "[[Equipo/Propiedades|Propiedades (Español)]]"'
            ))
            write(mastery, note(
                "Mastery Properties", ["Mastery Properties"], "tag_equipment", m,
                'related_es: "[[Equipo/PropiedadesDeMaestria|Propiedades de maestría (Español)]]"'
            ))
            a = body.index("## Properties")
            b = body.index("## Weapons Table")
            limpio = body[:a].rstrip() + "\n\n" + body[b:]
            weapons.write_text(frontmatter(w) + "\n" + limpio.rstrip() + "\n", encoding="utf-8")

    trade = root / "Trade Goods.md"
    if trade.exists():
        trade.unlink()

    idx = root / "Equipment-Index.md"
    if idx.exists():
        c = idx.read_text(encoding="utf-8")
        for a, b in [
            ("[[Coinage]]", "[[Coins]]"),
            ("[[Gear]]", "[[Adventuring Gear]]"),
            ("[[Transportation]]", "[[Mounts and Vehicles]]"),
        ]:
            c = c.replace(a, b)
        idx.write_text(c, encoding="utf-8")


def spells() -> None:
    root = EN / "Spells"
    src = root / "Spellcasting.md"
    if src.exists():
        raw = src.read_text(encoding="utf-8")
        gain = promote(section(raw, "## Gaining Spells", "## Casting Spells"))
        cast = promote(section(raw, "## Casting Spells", None))
        write(root / "Gaining Spells.md", note(
            "Gaining Spells", ["Gaining Spells"], "tag_spells", gain,
            'related_es: "[[Conjuros/ObtenerConjuros|Obtener conjuros (Español)]]"'
        ))
        write(root / "Casting Spells.md", note(
            "Casting Spells", ["Casting Spells"], "tag_spells", cast,
            'related_es: "[[Conjuros/LanzarConjuros|Lanzar conjuros (Español)]]"'
        ))
        src.unlink()

    old_idx = root / "Spells.md"
    if old_idx.exists():
        c = old_idx.read_text(encoding="utf-8")
        if "> Index of **Spells**" in c:
            c = c.replace("# Spells\n\n> Index of **Spells**", "# Spells\n\n## Chapter Structure\n\n- [[Spells]]\n- [[Gaining Spells]]\n- [[Casting Spells]]\n\n## Spell Catalog")
            old_idx.unlink()
            write(root / "Spells-Index.md", c)

    chapter = root / "Spells.md"
    if not chapter.exists():
        write(chapter, note(
            "Spells", ["Spells"], "tag_spells",
            "# Spells\n\n*This chapter describes how to gain and cast spells, in addition to providing detailed descriptions of every spell in the game.*",
            'related_es: "[[Conjuros/Conjuros|Conjuros (Español)]]"'
        ))

    idx = root / "Spells-Index.md"
    if idx.exists():
        c = idx.read_text(encoding="utf-8")
        if "- [[Spells]]" not in c:
            c = c.replace("## Chapter Structure\n\n", "## Chapter Structure\n\n- [[Spells]]\n")
            idx.write_text(c, encoding="utf-8")


def gameplay_toolbox() -> None:
    src = EN / "Gamemastering"
    dst = EN / "Gameplay Toolbox"
    dst.mkdir(exist_ok=True)

    mapping = {
        "Travel.md": "Travel Pace.md",
        "Creating a Background.md": "Creating a Background.md",
        "Environmental Effects.md": "Environmental Effects.md",
        "Fear and Mental Stress.md": "Fear and Mental Stress.md",
        "Poisons.md": "Poison.md",
        "Traps.md": "Traps.md",
        "Combat Encounters.md": "Combat Encounters.md",
    }
    for a, b in mapping.items():
        move(src / a, dst / b)

    curses = src / "Curses.md"
    contagions = src / "Magical Contagions.md"
    if curses.exists() and contagions.exists():
        cb = demote(strip_frontmatter(curses.read_text(encoding="utf-8")))
        mb = demote(strip_frontmatter(contagions.read_text(encoding="utf-8")))
        body = "# Curses and Magical Contagions\n\n" + cb.strip() + "\n\n" + mb.strip()
        write(dst / "Curses and Magical Contagions.md", note(
            "Curses and Magical Contagions", ["Curses and Magical Contagions"], "tag_gameplay_toolbox", body,
            'related_es: "[[HerramientasDelJuego/MaldicionesYEnfermedadesMagicas|Maldiciones y enfermedades mágicas (Español)]]"'
        ))
        curses.unlink()
        contagions.unlink()

    for name in ("Objects.md", "Gamemastering.md"):
        p = src / name
        if p.exists():
            p.unlink()
    if src.exists() and not any(src.iterdir()):
        src.rmdir()

    write(dst / "Gameplay Toolbox-Index.md", """# Gameplay Toolbox

- [[Travel Pace]]
- [[Creating a Background]]
- [[Curses and Magical Contagions]]
- [[Environmental Effects]]
- [[Fear and Mental Stress]]
- [[Poison]]
- [[Traps]]
- [[Combat Encounters]]
""")


def magic_items() -> None:
    src = EN / "Treasure"
    dst = EN / "Magic Items"
    if src.exists() and not dst.exists():
        src.rename(dst)
    if not dst.exists():
        return

    old_idx = dst / "Treasure.md"
    new_idx = dst / "Magic Items-Index.md"
    if old_idx.exists():
        old_idx.unlink()

    estructura = [
        "Magic Items",
        "Magic Item Categories",
        "Magic Item Rarity",
        "Activating a Magic Item",
        "The Next Dawn",
        "Cursed Items",
        "Magic Item Resilience",
        "Crafting Magic Items",
        "Sentient Magic Items",
        "Magic Item Rules",
    ]
    excluir = set(estructura) | {"Magic Items-Index"}
    catalogo = sorted(
        p.stem for p in dst.glob("*.md")
        if p.stem not in excluir
    )
    indice = [
        "# Magic Items",
        "",
        "## Chapter Structure",
        "",
        *[f"- [[{x}]]" for x in estructura],
        "",
        "## Magic Item Catalog",
        "",
        *[f"- [[{x}]]" for x in catalogo],
        "",
    ]
    write(new_idx, "\n".join(indice))


def monsters() -> None:
    root = EN / "Monsters"
    catalog = EN / "Monsters A-Z"
    catalog.mkdir(exist_ok=True)
    keep = {
        "Stat Block Overview.md",
        "Parts of a Stat Block.md",
        "Running a Monster.md",
        "Monsters-Index.md",
    }
    moved = []
    for p in list(root.glob("*.md")):
        if p.name in keep:
            continue
        move(p, catalog / p.name)
        moved.append(p.stem)

    all_entities = sorted(p.stem for p in catalog.glob("*.md") if not p.name.endswith("-Index.md"))
    write(catalog / "Monsters A-Z-Index.md", "# Monsters A-Z\n\n" + "\n".join(f"- [[{x}]]" for x in all_entities))
    write(root / "Monsters-Index.md", """# Monsters

- [[Stat Block Overview]]
- [[Parts of a Stat Block]]
- [[Running a Monster]]
""")

    if moved:
        targets = set(moved)
        for p in ES.rglob("*.md"):
            old = p.read_text(encoding="utf-8")
            new = old
            for stem in targets:
                new = new.replace(f"[[Monsters/{stem}|", f"[[Monsters A-Z/{stem}|")
                new = new.replace(f"[[Monsters/{stem}]]", f"[[Monsters A-Z/{stem}]]")
            if new != old:
                p.write_text(new, encoding="utf-8")


def index_hygiene() -> None:
    for src, dst in [
        (EN / "Animals" / "Animals.md", EN / "Animals" / "Animals-Index.md"),
        (EN / "Classes" / "Classes.md", EN / "Classes" / "Classes-Index.md"),
        (EN / "Rules Glossary" / "Index.md", EN / "Rules Glossary" / "Rules Glossary-Index.md"),
    ]:
        move(src, dst)


def update_links() -> None:
    reps = [
        ("[[Gameplay/Abilities#D20 Tests", "[[Playing the Game/D20 Tests"),
        ("[[Gameplay/Abilities#Proficiency", "[[Playing the Game/Proficiency"),
        ("[[Gameplay/Abilities|", "[[Playing the Game/The Six Abilities|"),
        ("[[Gameplay/Adventuring#Social Interaction", "[[Playing the Game/Social Interaction"),
        ("[[Gameplay/Adventuring#Exploration", "[[Playing the Game/Exploration"),
        ("[[Gameplay/Combat#Actions", "[[Playing the Game/Actions"),
        ("[[Gameplay/Combat#Combat", "[[Playing the Game/Combat"),
        ("[[Gameplay/Combat#Damage and Healing", "[[Playing the Game/Damage and Healing"),
        ("[[Gameplay/", "[[Playing the Game/"),
        ("[[Characterizations/Backgrounds", "[[Character Origins/Character Backgrounds"),
        ("[[Species/Species", "[[Character Origins/Character Species"),
        ("[[Species/", "[[Character Origins/"),
        ("[[Characterizations/Feats#Feat Descriptions", "[[Feats/Feat Descriptions"),
        ("[[Characterizations/Feats", "[[Feats/Feat Descriptions"),
        ("[[Gamemastering/Travel", "[[Gameplay Toolbox/Travel Pace"),
        ("[[Gamemastering/Creating a Background", "[[Gameplay Toolbox/Creating a Background"),
        ("[[Gamemastering/Curses", "[[Gameplay Toolbox/Curses and Magical Contagions"),
        ("[[Gamemastering/Magical Contagions", "[[Gameplay Toolbox/Curses and Magical Contagions"),
        ("[[Gamemastering/Environmental Effects", "[[Gameplay Toolbox/Environmental Effects"),
        ("[[Gamemastering/Fear and Mental Stress", "[[Gameplay Toolbox/Fear and Mental Stress"),
        ("[[Gamemastering/Poisons", "[[Gameplay Toolbox/Poison"),
        ("[[Gamemastering/Traps", "[[Gameplay Toolbox/Traps"),
        ("[[Gamemastering/Combat Encounters", "[[Gameplay Toolbox/Combat Encounters"),
        ("[[Treasure/", "[[Magic Items/"),
        ("[[Spells/Spellcasting#Gaining Spells", "[[Spells/Gaining Spells"),
        ("[[Spells/Spellcasting#Casting Spells", "[[Spells/Casting Spells"),
        ("[[Playing the Game/Adventuring", "[[Playing the Game/Exploration"),
        ("[[Equipment/Gear", "[[Equipment/Adventuring Gear"),
        ("[[Equipment/Coinage", "[[Equipment/Coins"),
        ("[[Equipment/Transportation", "[[Equipment/Mounts and Vehicles"),
        ("[[Classes/Paladín", "[[Classes/Paladin"),
    ]
    replace_all(ES, reps)
    replace_all(EN, reps)

    # ES es la referencia: las unidades equivalentes del TOC se enlazan archivo a archivo.
    pairs = [
        (ES / "Equipo" / "Propiedades.md",
         'related_en_section: "[[Equipment/Weapons#Properties|Properties (EN)]]"\nalignment_mode: "section"',
         'related_en: "[[Equipment/Properties|Properties (EN)]]"'),
        (ES / "Equipo" / "PropiedadesDeMaestria.md",
         'related_en_section: "[[Equipment/Weapons#Mastery Properties|Mastery Properties (EN)]]"\nalignment_mode: "section"',
         'related_en: "[[Equipment/Mastery Properties|Mastery Properties (EN)]]"'),
        (ES / "Dotes" / "DotesDeOrigen.md",
         'related_en_section: "[[Feats/Feat Descriptions#Origin Feats|Origin Feats (EN)]]"\nalignment_mode: "section"',
         'related_en: "[[Feats/Origin Feats|Origin Feats (EN)]]"'),
        (ES / "Dotes" / "DotesGenerales.md",
         'related_en_section: "[[Feats/Feat Descriptions#General Feats|General Feats (EN)]]"\nalignment_mode: "section"',
         'related_en: "[[Feats/General Feats|General Feats (EN)]]"'),
        (ES / "Dotes" / "DotesDeEstiloDeCombate.md",
         'related_en_section: "[[Feats/Feat Descriptions#Fighting Style Feats|Fighting Style Feats (EN)]]"\nalignment_mode: "section"',
         'related_en: "[[Feats/Fighting Style Feats|Fighting Style Feats (EN)]]"'),
        (ES / "Dotes" / "DotesDeDonEpico.md",
         'related_en_section: "[[Feats/Feat Descriptions#Epic Boon Feats|Epic Boon Feats (EN)]]"\nalignment_mode: "section"',
         'related_en: "[[Feats/Epic Boon Feats|Epic Boon Feats (EN)]]"'),
    ]
    for path, old, new in pairs:
        if path.exists():
            texto = path.read_text(encoding="utf-8").replace(old, new)
            path.write_text(texto, encoding="utf-8")

    replace_all(ES, [
        ("[[Equipment/Weapons#Properties", "[[Equipment/Properties"),
        ("[[Equipment/Weapons#Mastery Properties", "[[Equipment/Mastery Properties"),
        ("[[Feats/Feat Descriptions#Origin Feats", "[[Feats/Origin Feats"),
        ("[[Feats/Feat Descriptions#General Feats", "[[Feats/General Feats"),
        ("[[Feats/Feat Descriptions#Fighting Style Feats", "[[Feats/Fighting Style Feats"),
        ("[[Feats/Feat Descriptions#Epic Boon Feats", "[[Feats/Epic Boon Feats"),
    ])


def main() -> int:
    playing_the_game()
    character_origins_and_feats()
    equipment()
    spells()
    gameplay_toolbox()
    magic_items()
    monsters()
    index_hygiene()
    update_links()
    print("Estructura EN normalizada según el TOC oficial.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
