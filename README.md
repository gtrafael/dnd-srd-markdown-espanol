# SRD 5.2.1 bilingüe — corpus canónico

Este repositorio mantiene el **SRD 5.2.1 en español e inglés** que usa el proyecto `dungeon-agent`.

## Cómo funciona

```
main               ← fuente humana canónica y rama por defecto
  ES/              ← referencia estructural primaria
  EN/              ← espejo inglés
   │
   └── CI valida, genera índices y limpia
            │
            ▼
corpus             ← salida generada para IA
```

### `main`

Es la única rama que se corrige a mano.

- `ES/`: referencia estructural del proyecto.
- `EN/`: equivalente inglés de ES.
- conserva frontmatter, aliases y wikilinks para Obsidian.
- puede contener índices `(Alt)` generados para navegación; deben ser simétricos ES/EN y no contienen texto normativo.

Los PDF oficiales SRD 5.2.1 ES/EN son la autoridad sobre el contenido. Si ES y EN difieren estructuralmente, la diferencia debe estar justificada por el PDF oficial EN; no se conserva una diferencia solo porque existiera en las fuentes históricas.

### `corpus`

Se genera automáticamente desde `main`.

Elimina metadatos de Obsidian, wikilinks e índices de navegación, incluidos los `(Alt)`. **No se edita a mano.**

El workflow **Generar índices Obsidian** reconstruye automáticamente los `(Alt)` en `main`. El workflow **Generar corpus** publica la variante limpia en `corpus`.

## Relación con las fuentes originales

El proyecto ya no sincroniza automáticamente cambios de upstream. La procedencia queda fijada mediante una referencia histórica:

`upstream-baseline-2026-10-23`

A partir de ese baseline, `main` es nuestra fuente canónica. Cualquier corrección externa que interese se revisa y se incorpora de forma deliberada como un cambio propio, nunca mediante un merge automático de upstream.

Consulta [docs/FORK.md](docs/FORK.md) para la política de procedencia, ramas y versionado.

## Al modificar contenido

1. Corrige primero ES en `main`.
2. Revisa su equivalente EN.
3. Mantén `related_en` / `related_es` o una relación a sección cuando corresponda.
4. Deja que CI regenere `corpus`.
5. Comprueba que los workflows queden en verde.

Los controles principales son:

- **rápidos, en cada cambio:** TOC ES, simetría ES → EN, tablas y generación de `corpus`;
- **completo:** comparación con los PDF, estructura visual, cobertura, lineage y duplicados.

El workflow **Validar corpus completo** debe quedar en verde antes de aprobar una candidata. Sus informes son artefactos temporales de CI: no hay que mantenerlos ni versionarlos.

Las reglas estructurales están resumidas en [docs/CRITERIOS_CORPUS.md](docs/CRITERIOS_CORPUS.md).

## Releases y reproducibilidad

Las releases propias se etiquetan sobre `main`, que representa el estado humano canónico. Los consumidores automáticos deben fijar además el commit exacto de `corpus` que corresponde a la candidata aprobada.

De esta forma una release identifica la fuente mantenida y un commit de `corpus` identifica sin ambigüedad el material consumido por datasets, entrenamientos y benchmarks.

## Para agentes

Lee [AGENTS.md](AGENTS.md). Contiene únicamente el modelo mental y las reglas necesarias para trabajar en el repositorio.

## Licencia y procedencia

El contenido SRD se publica bajo **CC-BY-4.0**. Consulta [License.md](License.md) y [Legal.md](Legal.md) para atribución y detalles de procedencia.
