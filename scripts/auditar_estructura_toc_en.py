#!/usr/bin/env python3
"""Audita la estructura EN contra el TOC oficial del SRD 5.2.1.

La lista de capítulos y entradas directas procede de los bookmarks del PDF
oficial SRD_CC_v5.2.1.pdf. Los niveles inferiores se consideran encabezados
dentro del archivo padre. Callouts e entidades de catálogo son excepciones.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

EXPECTED = {
    "Playing the Game": [
        "Rhythm of Play", "The Six Abilities", "D20 Tests", "Proficiency",
        "Actions", "Social Interaction", "Exploration", "Combat",
        "Damage and Healing",
    ],
    "Character Creation": [
        "Choose a Character Sheet", "Create Your Character", "Level Advancement",
        "Starting at Higher Levels", "Multiclassing", "Trinkets",
    ],
    "Classes": [
        "Barbarian", "Bard", "Cleric", "Druid", "Fighter", "Monk", "Paladin",
        "Ranger", "Rogue", "Sorcerer", "Warlock", "Wizard",
    ],
    "Character Origins": ["Character Backgrounds", "Character Species"],
    "Feats": ["Feat Descriptions"],
    "Equipment": [
        "Coins", "Weapons", "Armor", "Tools", "Adventuring Gear",
        "Mounts and Vehicles", "Lifestyle Expenses", "Food, Drink, and Lodging",
        "Hirelings", "Spellcasting", "Magic Items", "Crafting Nonmagical Items",
        "Brewing Potions of Healing", "Scribing Spell Scrolls",
    ],
    "Spells": ["Gaining Spells", "Casting Spells"],
    "Gameplay Toolbox": [
        "Travel Pace", "Creating a Background", "Curses and Magical Contagions",
        "Environmental Effects", "Fear and Mental Stress", "Poison", "Traps",
        "Combat Encounters",
    ],
    "Magic Items": [
        "Magic Item Categories", "Magic Item Rarity", "Activating a Magic Item",
        "The Next Dawn", "Cursed Items", "Magic Item Resilience",
        "Crafting Magic Items", "Sentient Magic Items",
    ],
    "Monsters": ["Stat Block Overview", "Parts of a Stat Block", "Running a Monster"],
}

CATALOG_FOLDERS = {"Spells", "Magic Items", "Monsters A-Z", "Animals"}
CALLOUT_TAGS = {"callout", "recuadro"}
LEGACY_DIRS = {"Gameplay", "Characterizations", "Species", "Gamemastering", "Treasure"}


def key(text: str) -> str:
    s = unicodedata.normalize("NFKD", text)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", s.casefold())


def fm(text: str) -> str:
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---\n", 4)
    return text[4:end] if end >= 0 else ""


def h1(text: str) -> str | None:
    for line in text.splitlines():
        m = re.match(r"^#\s+(.+?)\s*$", line)
        if m:
            return m.group(1).strip()
    return None


def is_callout(text: str) -> bool:
    meta = fm(text).casefold()
    return any(tag in meta for tag in CALLOUT_TAGS)


def audit(root: Path) -> dict:
    failures = []
    chapters = []

    existing_dirs = {p.name for p in root.iterdir() if p.is_dir()}
    legacy = sorted(existing_dirs & LEGACY_DIRS)
    if legacy:
        failures.append({"tipo": "carpetas_legacy", "carpetas": legacy})

    for chapter, required in EXPECTED.items():
        folder = root / chapter
        if not folder.exists():
            failures.append({"tipo": "carpeta_faltante", "capitulo": chapter})
            chapters.append({"capitulo": chapter, "faltantes": required, "extras": []})
            continue

        docs = {}
        for p in folder.glob("*.md"):
            if p.name.endswith("-Index.md"):
                continue
            raw = p.read_text(encoding="utf-8")
            title = h1(raw)
            docs[p.name] = {
                "title": title,
                "key": key(title or ""),
                "callout": is_callout(raw),
            }

        required_keys = {key(x): x for x in required}
        missing = []
        bad_names = []
        for k, title in required_keys.items():
            matches = [(name, info) for name, info in docs.items() if info["key"] == k]
            if not matches:
                missing.append(title)
                continue
            if len(matches) == 1:
                name, _ = matches[0]
                if key(Path(name).stem) != k:
                    bad_names.append({"titulo": title, "archivo": name})

        extras = []
        if chapter not in CATALOG_FOLDERS:
            for name, info in docs.items():
                if info["callout"]:
                    continue
                if info["key"] in required_keys:
                    continue
                # Classes/Character Origins contienen entidades hoja explícitas.
                if chapter == "Character Origins" and name not in {"Character Backgrounds.md", "Character Species.md"}:
                    continue
                extras.append({"archivo": name, "h1": info["title"]})

        if missing:
            failures.append({"tipo": "faltantes", "capitulo": chapter, "titulos": missing})
        if bad_names:
            failures.append({"tipo": "nombres", "capitulo": chapter, "casos": bad_names})
        if extras:
            failures.append({"tipo": "extras", "capitulo": chapter, "casos": extras})

        chapters.append({
            "capitulo": chapter,
            "faltantes": missing,
            "nombres_incoherentes": bad_names,
            "extras": extras,
        })

    # Carpetas catálogo que deben existir por TOC de primer nivel.
    for name in ("Monsters A-Z", "Animals"):
        if not (root / name).exists():
            failures.append({"tipo": "carpeta_faltante", "capitulo": name})

    return {"fallos": len(failures), "incidencias": failures, "capitulos": chapters}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--en", type=Path, required=True)
    ap.add_argument("--salida", type=Path, required=True)
    args = ap.parse_args()

    out = audit(args.en)
    args.salida.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Fallos estructurales EN:", out["fallos"])
    for item in out["incidencias"]:
        print(json.dumps(item, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
