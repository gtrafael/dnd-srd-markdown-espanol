# SRD 5.2.1 bilingüe — corpus canónico

Este fork mantiene el **SRD 5.2.1 en español e inglés** que usa el proyecto `dungeon-agent`.

## Cómo funciona

```
upstream/main
     │
     ▼
custom/main        ← fuente humana editable
  ES/              ← referencia estructural primaria
  EN/              ← espejo inglés
     │
     └── CI valida y limpia
             │
             ▼
custom/corpus      ← salida generada para IA
```

### `custom/main`

Es la única rama que se corrige a mano.

- `ES/`: referencia estructural del proyecto.
- `EN/`: equivalente inglés de ES.
- conserva frontmatter, aliases y wikilinks para Obsidian.

Los PDF oficiales SRD 5.2.1 ES/EN son la autoridad sobre el contenido.  
Si ES y EN difieren estructuralmente, la diferencia debe estar justificada por el PDF oficial EN; no se conserva una diferencia solo porque viniera del upstream.

### `custom/corpus`

Se genera automáticamente desde `custom/main`.

Elimina metadatos de Obsidian e índices de navegación. **No se edita a mano.**

`custom/main` contiene una sola estructura **normativa** por idioma. Además puede contener carpetas `(Alt)` generadas para Obsidian: son solo índices de navegación, deben ser simétricas ES/EN y no contienen texto normativo.

`custom/corpus` elimina todos los índices, incluidos los `(Alt)`, por lo que conserva únicamente el contenido canónico.

El workflow **Generar índices Obsidian** reconstruye automáticamente los `(Alt)` desde las notas canónicas de `custom/main`.

## Al modificar contenido

1. Corrige primero ES.
2. Revisa su equivalente EN.
3. Mantén `related_en` / `related_es` o una relación a sección cuando corresponda.
4. Deja que CI regenere `custom/corpus`.
5. Comprueba que los workflows queden en verde.

Los controles principales son:

- **rápidos, en cada cambio:** TOC ES, simetría ES → EN, tablas y generación de `custom/corpus`;
- **completo:** comparación con los PDF, estructura visual, cobertura, lineage y duplicados.

El workflow **Validar corpus completo** debe quedar en verde antes de aprobar una candidata. Sus informes son artefactos temporales de CI: no hay que mantenerlos ni versionarlos.

Las reglas estructurales están resumidas en [docs/CRITERIOS_CORPUS.md](docs/CRITERIOS_CORPUS.md).

## Para agentes

Lee [AGENTS.md](AGENTS.md). Contiene únicamente el modelo mental y las reglas necesarias para trabajar en el repositorio.

## Licencia y procedencia

El contenido SRD se publica bajo **CC-BY-4.0**. Consulta [License.md](License.md) y [Legal.md](Legal.md) para atribución y detalles de procedencia.
