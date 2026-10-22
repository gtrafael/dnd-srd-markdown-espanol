#!/usr/bin/env python3
"""Normaliza tablas comprimidas horizontalmente por maquetación.

Regla: si la cabecera completa es exactamente dos copias de la misma
cabecera, la tabla representa dos bloques de registros del mismo dominio.
Se desempaqueta leyendo primero la mitad izquierda de arriba abajo y después
la mitad derecha. La transformación es idempotente y no altera tablas que no
cumplen exactamente este patrón. Los statblocks con cabecera MOD/SAVE quedan fuera porque
requieren una política específica.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEP = re.compile(r"^:?-{3,}:?$")

# Listas verificadas contra el SRD oficial y el gemelo EN. En el PDF se
# maquetan en varias columnas únicamente para ahorrar espacio; no existe una
# relación horizontal entre las celdas.
LISTAS_COMPRIMIDAS_VERIFICADAS = {
    ("Atacar", "Esconderse", "Preparar una"): (
        "Acción",
        [
            "Atacar",
            "Ayudar",
            "Buscar",
            "Correr",
            "Destrabarse",
            "Esconderse",
            "Esquivar",
            "Estudiar",
            "Influir",
            "Magia",
            "Preparar una acción",
            "Utilizar",
        ],
    ),
    ("Aberración", "Dragón", "Infernal"): (
        "Tipo de criatura",
        [
            "Aberración",
            "Autómata",
            "Bestia",
            "Celestial",
            "Cieno",
            "Dragón",
            "Elemental",
            "Feérico",
            "Gigante",
            "Humanoide",
            "Infernal",
            "Monstruosidad",
            "Muerto viviente",
            "Planta",
        ],
    ),
}


def cells(line: str) -> list[str]:
    s = line.strip()
    if not (s.startswith("|") and s.endswith("|")):
        return []
    return [x.strip() for x in s[1:-1].split("|")]


def is_sep(cs: list[str]) -> bool:
    return bool(cs) and all(SEP.match(x.replace(" ", "")) for x in cs)


def norm(s: str) -> str:
    s = re.sub(r"[*_]", "", s)
    return re.sub(r"\s+", " ", s).strip().casefold()


def repeated_halves(header: list[str]) -> bool:
    n = len(header)
    if n < 2 or n % 2:
        return False
    half = n // 2
    left = [norm(x) for x in header[:half]]
    right = [norm(x) for x in header[half:]]
    if left != right:
        return False
    # Statblock histórico EN: no aplicar esta regla genérica.
    if left == ["", "mod", "save"]:
        return False
    return True


def render_table(header: list[str], rows: list[list[str]]) -> list[str]:
    return [
        "| " + " | ".join(header) + " |",
        "|" + "|".join("---" for _ in header) + "|",
        *["| " + " | ".join(row) + " |" for row in rows],
    ]


def transform(text: str) -> tuple[str, int]:
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    changes = 0

    while i < len(lines):
        if i + 1 >= len(lines):
            out.append(lines[i])
            i += 1
            continue

        header = cells(lines[i])
        sep = cells(lines[i + 1])
        if not (header and sep and len(header) == len(sep) and is_sep(sep)):
            out.append(lines[i])
            i += 1
            continue

        j = i + 2
        rows = []
        while j < len(lines):
            row = cells(lines[j])
            if not row or len(row) != len(header):
                break
            rows.append(row)
            j += 1

        verificada = LISTAS_COMPRIMIDAS_VERIFICADAS.get(tuple(header))
        if verificada:
            nombre, valores = verificada
            out.extend(render_table([nombre], [[v] for v in valores]))
            changes += 1
        elif repeated_halves(header):
            half = len(header) // 2
            new_rows = []
            for side in (0, 1):
                start = side * half
                end = start + half
                for row in rows:
                    piece = row[start:end]
                    if any(x.strip() for x in piece):
                        new_rows.append(piece)
            out.extend(render_table(header[:half], new_rows))
            changes += 1
        else:
            out.extend(lines[i:j])

        i = j

    return "\n".join(out).rstrip() + "\n", changes


def main() -> int:
    total = 0
    files = 0
    for lang in ("ES", "EN"):
        for path in sorted((ROOT / lang).rglob("*.md")):
            old = path.read_text(encoding="utf-8")
            new, changes = transform(old)
            if changes:
                path.write_text(new, encoding="utf-8")
                total += changes
                files += 1
                print(f"{path.relative_to(ROOT)}: {changes}")
    print(f"Tablas normalizadas: {total}; archivos: {files}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
