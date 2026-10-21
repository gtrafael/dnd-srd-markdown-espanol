# Estrategia del fork

Este fork conserva el SRD 5.2.1 bilingüe como fuente de trabajo del proyecto `dungeon-agent`.

## Ramas

- `main`: espejo de upstream. No se introducen personalizaciones.
- `custom/main`: versión bilingüe corregida para uso humano y Obsidian. Conserva frontmatter, aliases, tags y relaciones ES↔EN cuando aportan navegación.
- `custom/corpus`: versión derivada para procesamiento automático. Mantiene el contenido canónico y la estructura lógica, pero elimina metadatos de Obsidian, wikilinks e imágenes que no aportan reglas.

Una futura rama de second brain/Obsidian podrá derivarse de `custom/main`, pero no forma parte del trabajo actual de normalización del SRD.

## Principios de corrección

1. Los PDF oficiales SRD 5.2.1 ES y EN son la autoridad normativa.
2. Toda corrección de contenido en un idioma obliga a revisar el concepto gemelo en el otro idioma.
3. La estructura canónica debe seguir la jerarquía lógica del libro, no la posición accidental causada por la maquetación.
4. Las tablas multipágina se consideran una única tabla lógica.
5. Los recuadros/callouts se inventarían y clasifican; no se convierten automáticamente en archivos separados.
6. `your5e/5e-srd-markdown` puede usarse como fuente secundaria de contraste para el inglés, nunca como autoridad.
7. Las correcciones reutilizables deben quedar documentadas y, cuando sea posible, cubiertas por controles de regresión en `dungeon-agent`.

## Relación con dungeon-agent

`dungeon-agent` no debe modificar directamente el contenido fuente. La limpieza que revele un error real debe corregirse primero en `custom/main` y reflejarse después en `custom/corpus`. El repositorio `dungeon-agent` se ocupa de lineage, validación contra PDF, datasets, benchmarks y entrenamiento.
