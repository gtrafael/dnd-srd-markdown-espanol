# Criterios del corpus

Estas son las reglas mínimas para mantener `main` y generar `corpus`.

## 1. Qué es autoridad

- Los PDF oficiales SRD 5.2.1 ES y EN mandan sobre el contenido.
- **ES es la referencia estructural primaria.**
- EN debe ser su espejo conceptual y, cuando el TOC lo permita, también documental.
- Una diferencia EN solo se acepta si está respaldada por el PDF oficial EN.

## 2. Estructura

El TOC oficial decide la estructura principal.

- capítulo → carpeta;
- unidad documental del TOC → archivo;
- niveles inferiores → encabezados dentro del archivo padre;
- entidades de catálogo (conjuros, objetos, monstruos, animales) → notas hoja;
- recuadros normativos → notas propias;
- una sola estructura normativa por idioma;
- los `(Alt)` están permitidos únicamente como índices generados para Obsidian, con la misma forma en ES y EN;
- los `(Alt)` no contienen texto normativo y nunca pasan a `corpus`.

La maquetación del PDF no crea relaciones ni archivos por sí sola.

## 3. Simetría ES → EN

Toda nota normativa ES debe apuntar a su equivalente EN mediante `related_en` o `related_en_section`.

Ese destino debe existir. El equivalente EN debe apuntar de vuelta cuando sea una relación archivo↔archivo.

`sin-equivalente` solo es válido si se ha comprobado en el PDF EN que la unidad realmente no existe.

No se fuerza a ES a adoptar la estructura histórica de EN.

## 4. Tablas

Las tablas representan datos, no la disposición visual de la página.

- columnas repetidas solo para ahorrar espacio → se desempaquetan;
- filas que son títulos de grupo → se convierten en subtítulos;
- tablas realmente multidimensionales → se conservan;
- una celda vacía nunca se interpreta automáticamente: se contrasta con el PDF.

## 5. Ramas

### `main`

Fuente humana editable:

- Markdown para Obsidian;
- índices `(Alt)` derivados y simétricos para navegar catálogos grandes;
- frontmatter, aliases y relaciones bilingües;
- contenido corregido;
- estructura canónica.

### `corpus`

Producto generado desde `main`:

- sin frontmatter;
- sin índices de navegación;
- wikilinks convertidos a texto;
- solo contenido útil para consumo automático.

**No se corrige a mano.**

La referencia `upstream-baseline-2026-10-23` conserva únicamente la procedencia histórica. No participa en el flujo de trabajo ni se sincroniza con `main`.

## 6. Gate

Cuando aparece una nueva familia de error:

1. se corrige en `main`;
2. se revisa el equivalente EN;
3. se añade una comprobación simple si puede repetirse;
4. se regenera `corpus`.

No se preparan datasets de entrenamiento hasta aprobar el corpus.
