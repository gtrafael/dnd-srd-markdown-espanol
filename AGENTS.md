# Guía para agentes

Este repositorio mantiene el **corpus canónico bilingüe del SRD 5.2.1**.

## Modelo mental

```
main              upstream heredado; no es nuestra fuente de trabajo
custom/main       fuente humana canónica
  ES/             referencia estructural primaria
  EN/             espejo inglés de ES
  (Alt)/          índices derivados para Obsidian, simétricos
custom/corpus     salida limpia sin índices ni metadatos
```

Los PDF oficiales ES y EN son la autoridad normativa del texto. Para la **estructura**, ES es la referencia: EN debe reflejarla salvo que el PDF oficial EN demuestre una diferencia real.

## Flujo normal

1. Editar únicamente `custom/main`.
2. Corregir primero ES.
3. Revisar y mantener el equivalente EN.
4. Los workflows validan estructura, tablas y simetría.
5. Si todo pasa, `custom/corpus` se regenera automáticamente.

**Nunca edites `custom/corpus` a mano.**

## Qué debe cumplir una corrección

- respetar el TOC oficial;
- no convertir maquetación visual en estructura falsa;
- mantener tablas con semántica correcta;
- conservar cada recuadro normativo como nota propia;
- mantener las relaciones `related_en` / `related_es`;
- contrastar cualquier duda con el PDF oficial.

Las reglas detalladas están en `docs/CRITERIOS_CORPUS.md`.

## Regla de simetría

La simetría se comprueba **ES → EN**.

Una nota normativa ES debe tener equivalente EN como archivo o sección. Si no lo tiene, se considera una incidencia hasta demostrar que el SRD inglés es realmente distinto.

Los índices `(Alt)` son una vista derivada: deben existir con la misma forma en ES y EN, pero nunca se consideran contenido normativo.

No se mantiene una estructura inglesa independiente solo porque el upstream histórico estuviera organizado de otra manera.

## Antes de terminar

Comprueba los workflows de `custom/main`. Si un nuevo tipo de error puede repetirse, añade una regresión sencilla al repositorio.

No añadas infraestructura, manifests o estados manuales si Git + los archivos Markdown permiten reconstruir la información.
