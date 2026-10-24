# Estrategia del repositorio

Este repositorio nació como fork para preparar el SRD 5.2.1 bilingüe, pero mantiene una línea propia. El objetivo no es sincronizar una copia de upstream, sino conservar una fuente canónica estable para `dungeon-agent`.

## Ramas

- `main`: fuente humana canónica, rama por defecto y único lugar donde se corrige contenido.
- `corpus`: salida **generada** desde `main` para procesamiento automático. No se corrige a mano.
- `upstream-baseline-2026-10-23`: referencia histórica e inmutable del antiguo `main` heredado.

## Política respecto a upstream

No se realizan merges ni rebases automáticos desde upstream.

Si aparece una corrección externa relevante:

1. se revisa el cambio;
2. se contrasta con el PDF oficial;
3. se aplica deliberadamente a `main`;
4. se revisa el equivalente ES/EN;
5. se ejecuta el QA;
6. `corpus` se regenera.

## Principios estructurales

1. Los PDF oficiales SRD 5.2.1 ES y EN son la autoridad normativa.
2. El índice/TOC oficial determina la estructura documental.
3. ES es la referencia estructural primaria; EN mantiene su espejo conceptual.
4. Una entrada directa del TOC puede ser una nota; una sección contenedora de catálogo puede ser una carpeta.
5. Las entidades de catálogo se mantienen como notas hoja.
6. La maquetación visual no crea estructura: los recuadros permanecen dentro de su capítulo o subcapítulo.
7. Toda carpeta canónica tiene un índice `00-*-Index.md` generado, solo con enlaces.
8. Los grandes catálogos pueden tener una vista `(Alt)` alfabética generada para Obsidian.
9. Índices normales y `(Alt)` son navegación humana y se excluyen de `corpus`.
10. Las tablas multipágina se normalizan por su semántica, no por su disposición física.

`your5e/5e-srd-markdown` puede utilizarse como fuente secundaria de contraste para el inglés, nunca como autoridad.

## Releases y etiquetas

Las releases propias se etiquetan sobre `main`.

El commit exacto de `corpus` utilizado por una candidata se fija en `dungeon-agent`. Así los datasets, CPT, SFT y benchmarks siguen siendo reproducibles aunque `main` continúe evolucionando.

## Relación con dungeon-agent

Las correcciones de contenido viven aquí. `dungeon-agent` consume un commit exacto de `corpus` y se ocupa de candidatas, datasets, benchmarks, entrenamiento e integración posterior.

Los criterios detallados están en [CRITERIOS_CORPUS.md](CRITERIOS_CORPUS.md).
