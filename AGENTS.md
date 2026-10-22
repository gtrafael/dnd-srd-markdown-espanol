# Guía para agentes

Este repositorio mantiene el **corpus canónico bilingüe del SRD 5.2.1**.

## Modelo mental

```
main              fuente humana canónica y rama por defecto
  ES/             referencia estructural primaria
  EN/             espejo inglés de ES
  (Alt)/          índices derivados para Obsidian, simétricos
corpus            salida limpia generada, sin índices ni metadatos

upstream-baseline-2026-10-23
                  referencia histórica de procedencia; no se sincroniza
```

Los PDF oficiales ES y EN son la autoridad normativa del texto. Para la **estructura**, ES es la referencia: EN debe reflejarla salvo que el PDF oficial EN demuestre una diferencia real.

## Flujo normal

1. Editar únicamente `main`.
2. Corregir primero ES.
3. Revisar y mantener el equivalente EN.
4. El workflow **Generar índices Obsidian** reconstruye los `(Alt)` desde las notas canónicas.
5. Los workflows validan estructura, tablas y simetría.
6. `corpus` se genera desde `main` sin índices ni metadatos.

**Nunca edites `corpus` a mano.**

## Relación con upstream

No se hacen merges ni rebases automáticos desde upstream. Si una fuente externa publica una corrección útil, se contrasta con los PDF oficiales y se incorpora deliberadamente en `main` mediante un commit propio.

La referencia `upstream-baseline-2026-10-23` conserva el punto histórico desde el que se consolidó el proyecto.

## Qué debe cumplir una corrección

- respetar el TOC oficial;
- no convertir maquetación visual en estructura falsa;
- mantener tablas con semántica correcta;
- conservar cada recuadro normativo como nota propia;
- mantener las relaciones `related_en` / `related_es`;
- contrastar cualquier duda con el PDF oficial.

Las reglas detalladas están en `docs/CRITERIOS_CORPUS.md`.

## Regla de simetría

La simetría se comprueba **ES → EN**.

Una nota normativa ES debe tener equivalente EN como archivo o sección. Si no lo tiene, se considera una incidencia hasta demostrar que el SRD inglés es realmente distinto.

Los índices `(Alt)` son una vista derivada: deben existir con la misma forma en ES y EN, pero nunca se consideran contenido normativo.

No se mantiene una estructura inglesa independiente solo porque las fuentes históricas estuvieran organizadas de otra manera.

## Antes de terminar

Comprueba los workflows de `main`. Si un nuevo tipo de error puede repetirse, añade una regresión sencilla al repositorio.

No añadas infraestructura, manifests o estados manuales si Git + los archivos Markdown permiten reconstruir la información.
