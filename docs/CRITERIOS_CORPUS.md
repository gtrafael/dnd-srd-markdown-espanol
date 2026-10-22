# Criterios del corpus canónico

Este documento define las reglas estructurales que deben seguir `custom/main` y la rama derivada `custom/corpus`. Su objetivo es evitar que decisiones accidentales de maquetación del PDF se conviertan en estructura o relaciones falsas dentro del corpus.

## 1. Autoridades

1. Los PDF oficiales SRD 5.2.1 ES y EN son la autoridad normativa del contenido.
2. El índice/TOC oficial determina la estructura documental: carpetas, archivos y relaciones padre-hijo principales.
3. La maquetación visual del cuerpo del PDF no crea por sí sola archivos nuevos.
4. `your5e/5e-srd-markdown` es únicamente una fuente secundaria de contraste para el inglés.

## 2. Archivos y encabezados

- Los capítulos principales del índice/TOC determinan las carpetas canónicas.
- Una entrada directa del capítulo se representa como archivo propio cuando contiene reglas o contenido normativo.
- Los niveles inferiores del TOC permanecen como `##`, `###`, etc. dentro del archivo padre.
- Un encabezado visible en el cuerpo que no aparece como entrada equivalente del TOC permanece dentro del archivo padre.
- Ejemplo: `Armas`, `Propiedades` y `Propiedades de maestría` son unidades documentales porque aparecen en el índice.
- Ejemplo: `Competencia con armas` permanece dentro de `Armas.md` porque no aparece como unidad independiente en el índice.

Esta regla evita que el tamaño o estilo tipográfico de un encabezado decida arbitrariamente la estructura.

### 2.1 El TOC se respeta por idioma

El TOC oficial ES y el TOC oficial EN no siempre tienen la misma granularidad. Cada idioma sigue su propio TOC.

Ejemplo: en ES, `Propiedades` y `Propiedades de maestría` son unidades documentales directas de `Equipo`; en EN, `Properties` y `Mastery Properties` son hijos de `Weapons` y permanecen como secciones dentro de `Weapons.md`.

La alineación bilingüe puede por tanto ser archivo↔archivo, archivo↔sección o uno↔varios. Nunca se modifica la jerarquía oficial de un idioma para forzar una simetría 1:1.

### 2.2 Notas hoja de catálogos

Las entidades enumeradas dentro de catálogos normativos pueden conservarse como notas hoja aunque no aparezcan individualmente en el índice principal. Esto incluye, entre otros, conjuros, objetos mágicos, monstruos y animales.

El nodo estructural del catálogo sigue estando determinado por el TOC; las notas hoja no crean nuevos niveles jerárquicos.

## 3. Excepción: recuadros/callouts

Los recuadros grises constituyen la única excepción estructural al TOC.

- Cada recuadro normativo se conserva como una nota propia.
- El nombre del archivo debe corresponder al título del recuadro.
- El primer encabezado `#` debe corresponder al nombre semántico del archivo.
- El lineage conserva capítulo, sección, página y, cuando sea útil, posición física.
- Los gemelos ES/EN se enlazan cuando exista equivalencia real.

Ejemplos:

- `VenderEquipo.md` → `# Vender equipo`
- `ArmasImprovisadas.md` → `# Armas improvisadas`
- `LasExcepcionesSeImponenALasReglasGenerales.md`

No se agrupan todos los recuadros del capítulo en una nota genérica porque eso elimina identidad, lineage y referencias precisas.

## 4. Tablas: representar semántica, no maquetación

Una tabla del PDF se normaliza según qué información representa.

### 4.1 Tabla unidimensional comprimida en varias columnas

Si el PDF usa dos o más columnas únicamente para ahorrar espacio y todas representan el mismo campo, el Markdown canónico debe desempaquetarla.

Ejemplo visual:

| Idioma | Idioma |
|---|---|
| A | F |
| B | G |

se representa como:

| Idioma |
|---|
| A |
| B |
| … |
| F |
| G |

No se debe enseñar al modelo una relación horizontal inexistente entre dos elementos independientes.

### 4.2 Pares de campos repetidos

Si una tabla repite el mismo esquema horizontal, por ejemplo:

`Puntuación | Coste | Puntuación | Coste`

y cada pareja representa registros independientes del mismo dominio, debe estudiarse su conversión a una única tabla:

`Puntuación | Coste`.

Solo se transforma automáticamente cuando la equivalencia semántica sea inequívoca.

### 4.3 Encabezados de grupo incrustados como filas

Una fila cuyo primer campo nombra una categoría y cuyos demás campos están vacíos no debe tratarse como un registro si en realidad funciona como encabezado de grupo.

Ejemplo:

`Armas cuerpo a cuerpo sencillas | | | | |`

se convierte en un subtítulo y una tabla propia dentro del mismo archivo:

`### Armas cuerpo a cuerpo sencillas`

No se crean archivos exclusivos para esas tablas.

### 4.4 Tablas realmente multidimensionales

Las tablas cuyas columnas representan atributos distintos de un mismo registro se conservan como tablas.

Una celda vacía no se elimina automáticamente: puede ser un dato perdido. Antes de reinterpretarla como estructura debe contrastarse con el PDF y el gemelo bilingüe.

## 5. Simetría ES/EN

Toda corrección estructural o normativa en un idioma obliga a revisar el concepto equivalente en el otro.

La simetría buscada es conceptual, no necesariamente documental ni de maquetación. No se fuerzan pares 1:1 cuando el contenido no sea realmente equivalente. Si los TOC ES/EN usan distinta granularidad, la relación se modela mediante sección o relación uno-a-varios.

## 6. Separación de responsabilidades

### custom/main

- bóveda bilingüe corregida para uso humano y Obsidian;
- estructura documental canónica;
- recuadros como notas propias;
- tablas semánticamente normalizadas;
- frontmatter, aliases y relaciones ES↔EN.

### custom/corpus

Se genera reproduciblemente desde `custom/main` y:

- elimina frontmatter;
- resuelve wikilinks;
- elimina índices de navegación y duplicados estructurales;
- conserva el contenido normativo y la estructura semántica;
- exporta relaciones ES↔EN a metadata lateral.

`custom/corpus` no se corrige a mano.

## 7. Gate G1

Cada nueva familia de error descubierta durante la revisión humana reabre G1 hasta que:

1. se define una regla general;
2. se audita el corpus completo para esa familia;
3. se corrigen ES y EN;
4. se añade QA/regresión cuando sea automatizable;
5. se genera una nueva candidata.

Los workflows de QA deben fallar si reaparece una desviación estructural del TOC o una tabla candidata a normalización semántica.

No se preparan datasets CPT/SFT antes de la aprobación explícita de G1.
