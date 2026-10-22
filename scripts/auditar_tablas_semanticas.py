#!/usr/bin/env python3
"""Audita patrones de tablas Markdown que pueden reflejar maquetación del PDF.

No modifica contenido. Genera un JSON con candidatos para revisión:
- cabeceras repetidas horizontalmente (A|B|A|B, Idioma|Idioma, etc.);
- tablas unidimensionales comprimidas en varias columnas;
- filas que parecen encabezados de grupo incrustados;
- filas con celdas vacías que no son claramente agrupadores.

El objetivo es separar estructura semántica de maquetación antes de CPT/SFT.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SEP_RE = re.compile(r"^:?-{3,}:?$")


def celda_normalizada(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())


def parse_fila(linea: str) -> list[str] | None:
    s = linea.strip()
    if not (s.startswith("|") and s.endswith("|")):
        return None
    return [celda_normalizada(x) for x in s[1:-1].split("|")]


def es_separador(celdas: list[str]) -> bool:
    return bool(celdas) and all(SEP_RE.match(x.replace(" ", "")) for x in celdas)


def periodo_repetido(celdas: list[str]) -> int | None:
    n = len(celdas)
    for p in range(1, n // 2 + 1):
        if n % p:
            continue
        base = celdas[:p]
        if base * (n // p) == celdas:
            return p
    return None


def tablas(texto: str) -> list[dict]:
    lineas = texto.splitlines()
    out = []
    i = 0
    while i < len(lineas) - 1:
        cab = parse_fila(lineas[i])
        sep = parse_fila(lineas[i + 1])
        if not cab or not sep or len(cab) != len(sep) or not es_separador(sep):
            i += 1
            continue

        inicio = i
        filas = []
        i += 2
        while i < len(lineas):
            fila = parse_fila(lineas[i])
            if not fila or len(fila) != len(cab):
                break
            filas.append(fila)
            i += 1

        titulo = ""
        for j in range(inicio - 1, max(-1, inicio - 8), -1):
            t = lineas[j].strip()
            if not t:
                continue
            if t.startswith("#"):
                titulo = re.sub(r"^#+\s*", "", t)
            else:
                titulo = t
            break

        out.append({
            "linea": inicio + 1,
            "titulo_contexto": titulo,
            "cabecera": cab,
            "filas": filas,
        })
    return out


def analizar_tabla(tabla: dict) -> dict:
    cab = tabla["cabecera"]
    filas = tabla["filas"]
    periodo = periodo_repetido(cab)

    statblock_en = cab == ["", "MOD", "SAVE", "", "MOD", "SAVE"]
    repetida = periodo is not None and periodo < len(cab) and not statblock_en
    unidimensional = bool(repetida and periodo == 1)

    filas_grupo = []
    filas_vacias_sospechosas = []
    for idx, fila in enumerate(filas, start=tabla["linea"] + 2):
        vacias = [x == "" for x in fila]
        no_vacias = [x for x in fila if x not in {"", "—", "-", "–"}]
        # Un agrupador típico tiene texto solo en la primera celda.
        if len(fila) > 1 and fila[0] not in {"", "—", "-", "–"} and all(
            x in {"", "—", "-", "–"} for x in fila[1:]
        ):
            filas_grupo.append({"linea": idx, "fila": fila})
        elif len(fila) > 1 and any(vacias):
            filas_vacias_sospechosas.append({"linea": idx, "fila": fila})

    # Si el esquema horizontal se repite, cada bloque debe poder considerarse
    # un registro independiente del mismo dominio.
    bloques = []
    if repetida and periodo:
        for fila in filas:
            bloques.append([
                fila[j:j+periodo] for j in range(0, len(fila), periodo)
            ])

    return {
        **{k: tabla[k] for k in ("linea", "titulo_contexto", "cabecera")},
        "columnas": len(cab),
        "filas": len(filas),
        "periodo_cabecera": periodo,
        "cabecera_repetida": repetida,
        "unidimensional_comprimida": unidimensional,
        "statblock_en": statblock_en,
        "filas_grupo": filas_grupo,
        "filas_vacias_sospechosas": filas_vacias_sospechosas,
        "bloques_muestra": bloques[:5],
    }


def auditar_raiz(root: Path) -> dict:
    archivos = []
    resumen = {
        "archivos_con_tablas": 0,
        "tablas": 0,
        "cabecera_repetida": 0,
        "unidimensional_comprimida": 0,
        "tablas_con_filas_grupo": 0,
        "tablas_con_vacios_sospechosos": 0,
    }

    for path in sorted(root.rglob("*.md")):
        texto = path.read_text(encoding="utf-8")
        ts = [analizar_tabla(t) for t in tablas(texto)]
        if not ts:
            continue
        resumen["archivos_con_tablas"] += 1
        resumen["tablas"] += len(ts)
        resumen["cabecera_repetida"] += sum(t["cabecera_repetida"] for t in ts)
        resumen["unidimensional_comprimida"] += sum(t["unidimensional_comprimida"] for t in ts)
        resumen["tablas_con_filas_grupo"] += sum(bool(t["filas_grupo"]) for t in ts)
        resumen["tablas_con_vacios_sospechosos"] += sum(bool(t["filas_vacias_sospechosas"]) for t in ts)

        candidatos = [
            t for t in ts
            if t["cabecera_repetida"]
            or t["filas_grupo"]
            or t["filas_vacias_sospechosas"]
        ]
        if candidatos:
            archivos.append({
                "archivo": path.relative_to(root).as_posix(),
                "candidatos": candidatos,
            })

    return {"resumen": resumen, "archivos": archivos}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--es", type=Path, required=True)
    ap.add_argument("--en", type=Path, required=True)
    ap.add_argument("--salida", type=Path, required=True)
    args = ap.parse_args()

    out = {
        "es": auditar_raiz(args.es),
        "en": auditar_raiz(args.en),
    }
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    total_candidatos = 0
    for lang in ("es", "en"):
        print(lang, json.dumps(out[lang]["resumen"], ensure_ascii=False))
        print("candidatos", len(out[lang]["archivos"]))
        total_candidatos += len(out[lang]["archivos"])
    return 1 if total_candidatos else 0


if __name__ == "__main__":
    raise SystemExit(main())
