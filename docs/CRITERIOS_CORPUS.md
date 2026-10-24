# Criterios del corpus

Estas son las reglas mínimas para mantener `main` y generar `corpus`.

## 1. Autoridad

- Los PDF oficiales SRD 5.2.1 ES y EN mandan sobre el contenido.
- **ES es la referencia estructural primaria.**
- EN debe ser su espejo conceptual y, cuando el TOC lo permita, también documental.
- Una diferencia EN solo se acepta si está respaldada por el PDF oficial EN.

## 2. Estructura canónica

El TOC oficial decide la estructura documental.

- capítulo de nivel superior → carpeta;
- unidad directa del capítulo → archivo;
- sección contenedora de un catálogo → subcarpeta;
- niveles inferiores → encabezados dentro del archivo padre;
- entidades de catálogo → notas hoja;
- la maquetación visual no crea estructura por sí sola.

Esto último incluye explícitamente los recuadros: **un recuadro nunca crea una nota independiente solo por ser un recuadro**. Su contenido permanece dentro de la nota padre correspondiente.

Ejemplos:

```
Conjuros/
  LanzarConjuros.md
  ObtenerConjuros.md
  DescripcionesDeConjuros/
    ...

ObjetosMagicos/
  CategoriasDeObjetosMagicos.md
  ...
  ObjetosMagicosDeLaAALaZ/
    ...
```

## 3. Navegación humana

Toda carpeta canónica contiene exactamente un índice generado:

`00-<Nombre>-Index.md`

Los índices:

- contienen solo enlaces;
- no contienen contadores, totales ni estado manual;
- no son contenido normativo;
- no pasan a `corpus`.

Los grandes catálogos pueden tener además una carpeta `(Alt)` generada con navegación por bloques alfabéticos. Esa vista es exclusivamente humana y tampoco pasa a `corpus`.

## 4. Simetría ES → EN

Toda nota normativa ES debe apuntar a su equivalente EN mediante `related_en` o `related_en_section`.

Ese destino debe existir. El equivalente EN debe apuntar de vuelta cuando sea una relación archivo↔archivo.

`sin-equivalente` solo es válido si se ha comprobado en el PDF EN que la unidad realmente no existe.

La simetría se aplica también a las carpetas contenedoras de catálogos.

## 5. Tablas

Las tablas representan datos, no la disposición visual de la página.

- columnas repetidas solo para ahorrar espacio → se desempaquetan;
- filas que son títulos de grupo → se convierten en subtítulos;
- tablas realmente multidimensionales → se conservan;
- una celda vacía nunca se interpreta automáticamente: se contrasta con el PDF.

## 6. Ramas

### `main`

Fuente humana editable y canónica:

- Markdown para Obsidian;
- estructura basada en el TOC;
- índices `00-*-Index.md` derivados;
- índices `(Alt)` derivados para catálogos grandes;
- frontmatter, aliases y relaciones bilingües;
- contenido corregido.

### `corpus`

Producto generado desde `main`:

- sin frontmatter;
- sin índices de navegación;
- sin carpetas `(Alt)`;
- wikilinks convertidos a texto;
- solo contenido útil para consumo automático.

**No se corrige a mano.**

La referencia `upstream-baseline-2026-10-23` conserva únicamente la procedencia histórica.

## 7. Gate

Cuando aparece una nueva familia de error:

1. se corrige en `main`;
2. se revisa el equivalente EN;
3. se añade una comprobación sencilla si puede repetirse;
4. se regeneran los índices;
5. se regenera `corpus`.

No se preparan datasets de entrenamiento hasta aprobar el corpus.
