# SRD 5.2.1 bilingüe — corpus canónico

Este repositorio mantiene el **SRD 5.2.1 en español e inglés** que usa el proyecto `dungeon-agent`.

## Modelo del repositorio

```
main
├── ES/                         fuente humana canónica
├── EN/                         espejo inglés
├── 00-*-Index.md               navegación humana derivada
└── *(Alt)/                     navegación alfabética derivada
        │
        └── CI valida y limpia
                │
                ▼
corpus                           contenido canónico para IA
```

### `main`

Es la única rama que se corrige a mano.

- Los PDF oficiales SRD 5.2.1 ES/EN son la autoridad normativa.
- El **índice/TOC oficial define la estructura documental**.
- ES es la referencia estructural y EN mantiene su espejo conceptual.
- Los recuadros del PDF permanecen dentro de su capítulo o subcapítulo; la maquetación visual no crea notas independientes.
- Las entidades de catálogo sí tienen notas hoja individuales.

Los grandes catálogos reflejan también sus contenedores del TOC. Por ejemplo:

```
Conjuros/
├── 00-Conjuros-Index.md
├── Conjuros.md
├── ObtenerConjuros.md
├── LanzarConjuros.md
└── DescripcionesDeConjuros/
    ├── 00-DescripcionesDeConjuros-Index.md
    └── ...

ObjetosMagicos/
├── 00-ObjetosMagicos-Index.md
├── ...
└── ObjetosMagicosDeLaAALaZ/
    ├── 00-ObjetosMagicosDeLaAALaZ-Index.md
    └── ...
```

### Navegación humana

Toda carpeta canónica tiene exactamente un índice generado `00-<Nombre>-Index.md`.

Estos índices:

- contienen únicamente enlaces;
- no contienen números de archivos ni totales;
- se regeneran automáticamente;
- no son contenido normativo.

Los catálogos grandes —conjuros, objetos mágicos, monstruos A-Z y animales— tienen además una vista `(Alt)` por bloques alfabéticos. Es una segunda forma de **navegar**, no una segunda estructura canónica.

Por tanto:

- `00-*-Index.md` = mapa estructural de una carpeta;
- `(Alt)` = navegación alfabética cómoda para humanos;
- ninguno de los dos pasa a `corpus`.

### `corpus`

Se genera automáticamente desde `main`.

Elimina:

- frontmatter y metadatos de Obsidian;
- todos los índices `00-*-Index.md`;
- todas las carpetas `(Alt)`;
- wikilinks como sintaxis de navegación.

Conserva solo el contenido canónico útil para procesamiento automático. **No se edita a mano.**

## Relación con las fuentes originales

El proyecto ya no sincroniza automáticamente cambios de upstream. La procedencia queda fijada mediante:

`upstream-baseline-2026-10-23`

Cualquier corrección externa relevante se contrasta con los PDF oficiales y se incorpora deliberadamente a `main`.

Consulta [docs/FORK.md](docs/FORK.md) para la política de procedencia y [docs/CRITERIOS_CORPUS.md](docs/CRITERIOS_CORPUS.md) para las reglas estructurales.

## Al modificar contenido

1. Corrige primero ES en `main`.
2. Revisa el equivalente EN.
3. Mantén las relaciones `related_en` / `related_es` o a sección cuando corresponda.
4. Deja que CI regenere los índices y `corpus`.
5. Comprueba que los workflows queden en verde.

Los controles principales son:

- **rápidos:** TOC, simetría ES → EN, tablas e índices;
- **completo:** comparación con los PDF, estructura visual, cobertura, lineage y duplicados.

No se preparan datasets de entrenamiento hasta aprobar el corpus.

## Releases y reproducibilidad

Las releases propias se etiquetan sobre `main`. Los consumidores automáticos fijan además el commit exacto de `corpus` utilizado, de modo que datasets, entrenamientos y benchmarks sean reproducibles aunque `main` continúe evolucionando.

## Wikilinks automáticos

En la rama experimental, `wikilinks_auto` representa **menciones textuales
desambiguadas** a entidades físicas de la misma bóveda. No implica por sí solo
una relación reglística, causalidad, pertenencia ni relevancia mecánica.

Ejemplos deliberadamente válidos incluyen una mención a Murciélago/Bat desde
Bola de fuego/Fireball cuando aparece en el componente material, o varios
destinos cuando dos entidades físicas comparten nombre.

El generador puede aplicar reglas deterministas para identificar correctamente
la entidad mencionada (longest-match, bloqueadores estructurales y contexto
estructurado para nombres ambiguos), pero no intenta decidir si la mención es
"importante".

Consulta [docs/experimento-wikilinks-es.md](docs/experimento-wikilinks-es.md)
para el contrato completo y las invariantes del experimento.

## Para agentes

Lee [AGENTS.md](AGENTS.md).

## Licencia y procedencia

El contenido SRD se publica bajo **CC-BY-4.0**. Consulta [License.md](License.md) y [Legal.md](Legal.md).
