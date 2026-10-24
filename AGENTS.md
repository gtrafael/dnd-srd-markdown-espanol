# Guía para agentes

Este repositorio mantiene el **corpus canónico bilingüe del SRD 5.2.1**.

## Modelo mental

```
main
  ES/             referencia estructural primaria
  EN/             espejo inglés de ES
  00-*-Index.md   índices derivados de navegación
  *(Alt)/         vistas alfabéticas derivadas

corpus            salida limpia, sin navegación ni metadatos

upstream-baseline-2026-10-23
                  referencia histórica de procedencia
```

Los PDF oficiales ES y EN son la autoridad normativa.

## Regla estructural

La estructura la decide el **TOC oficial**, no la maquetación del PDF.

- capítulo → carpeta;
- unidad directa del capítulo → archivo;
- sección contenedora de catálogo → subcarpeta;
- niveles inferiores → encabezados del archivo padre;
- entidad de catálogo → nota hoja;
- recuadro/callout → permanece dentro de su padre.

Un recuadro no crea una nota independiente solo por estar destacado visualmente.

## Navegación

Toda carpeta canónica debe tener exactamente un `00-<Nombre>-Index.md` generado.

Los catálogos grandes pueden tener además una carpeta `(Alt)` alfabética. Ambos son navegación humana derivada y nunca contenido normativo.

No edites índices generados manualmente.

## Flujo normal

1. Edita únicamente `main`.
2. Corrige primero ES.
3. Revisa el equivalente EN.
4. Mantén las relaciones bilingües.
5. Regenera los índices.
6. Ejecuta los gates de estructura, simetría y tablas.
7. `corpus` se genera automáticamente.

**Nunca edites `corpus` a mano.**

## Relación con upstream

No se hacen merges ni rebases automáticos desde upstream. Una corrección externa útil se contrasta con los PDF oficiales y se incorpora deliberadamente como un cambio propio.

## Antes de terminar

Comprueba los workflows de `main`. Si un nuevo tipo de error puede repetirse, añade una regresión sencilla.

No añadas estados manuales, contadores ni infraestructura si Git y los Markdown permiten reconstruirlos.
