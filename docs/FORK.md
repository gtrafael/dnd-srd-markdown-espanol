# Estrategia del repositorio

Este repositorio nació como fork para preparar el SRD 5.2.1 bilingüe, pero desde el corte de octubre de 2026 mantiene una línea propia. El objetivo ya no es sincronizar una copia de upstream, sino conservar una fuente canónica estable para `dungeon-agent`.

## Ramas

- `main`: fuente humana canónica, rama por defecto y único lugar donde se corrige contenido. Conserva frontmatter, aliases, tags, relaciones ES↔EN e índices útiles para Obsidian.
- `corpus`: rama **generada** desde `main` para procesamiento automático. Mantiene el contenido normativo y la estructura lógica, pero elimina metadatos de Obsidian, wikilinks, índices de navegación e imágenes que no aportan reglas. No se corrige a mano.
- `upstream-baseline-2026-10-23`: referencia histórica e inmutable del antiguo `main` heredado. Sirve para procedencia, no para desarrollo.

Las ramas históricas `custom/main` y `custom/corpus` dejan de ser referencias de trabajo. Ningún consumidor nuevo debe depender de ellas.

## Política respecto a upstream

No se realizan merges ni rebases automáticos desde upstream.

El contenido es esencialmente estático y nuestra estructura, simetría ES/EN, navegación Obsidian y controles de calidad son parte del producto. Una sincronización indiscriminada podría alterar el corpus y romper la comparabilidad de datasets o experimentos.

Si aparece una corrección externa relevante:

1. se revisa el cambio externo;
2. se contrasta con el PDF oficial correspondiente;
3. se aplica deliberadamente a `main`;
4. se revisa el concepto gemelo ES/EN;
5. se ejecuta el QA normal;
6. `corpus` se regenera.

La procedencia original se conserva mediante Git, `License.md`, `Legal.md` y la referencia histórica del baseline.

## Principios de corrección

1. Los PDF oficiales SRD 5.2.1 ES y EN son la autoridad normativa.
2. Toda corrección de contenido en un idioma obliga a revisar el concepto gemelo en el otro idioma.
3. El índice/TOC oficial determina la estructura documental principal. Un encabezado del cuerpo que no figure como unidad equivalente en el TOC permanece dentro de su archivo padre.
4. Los recuadros/callouts normativos son la excepción al TOC: cada recuadro se conserva como nota propia, con nombre y título correspondientes a su encabezado.
5. Las tablas multipágina se consideran una única tabla lógica y se normalizan por su semántica, no por cómo fueron comprimidas para caber en la página.
6. `your5e/5e-srd-markdown` puede usarse como fuente secundaria de contraste para el inglés, nunca como autoridad.
7. Las correcciones reutilizables deben quedar documentadas y, cuando sea posible, cubiertas por controles de regresión.

## Releases y etiquetas

Las releases propias del proyecto se etiquetan sobre `main`.

Una release expresa el estado canónico humano. El commit exacto de `corpus` usado por una candidata de entrenamiento se fija aparte en `dungeon-agent`, para que datasets, CPT, SFT y benchmarks sigan siendo reproducibles aunque `main` continúe evolucionando.

No se reutilizan tags de upstream para representar versiones propias.

## Relación con dungeon-agent

`dungeon-agent` no debe convertirse en el lugar donde viven correcciones de contenido. Si el QA revela un error real, se corrige primero en `main`, se revisa el concepto gemelo ES/EN y luego se regenera `corpus`.

`dungeon-agent` consume un commit exacto de la rama `corpus` y se ocupa de fijar candidatas, datasets, benchmarks, entrenamiento e integración posterior.

Los criterios detallados y ejemplos normativos están definidos en [CRITERIOS_CORPUS.md](CRITERIOS_CORPUS.md). Ante una duda estructural, ese documento prevalece sobre decisiones históricas del extractor.
