# Experimento de wikilinks automáticos en ES

Esta rama prueba una capa de relaciones automática para Obsidian sin modificar
el contenido Markdown de las notas.

## Objetivo

Buscar menciones textuales a un conjunto controlado de notas y registrar esas
relaciones únicamente en el frontmatter:

```yaml
wikilinks_auto:
  - "[[Clases/Mago|Mago]]"
  - "[[Conjuros/BolaDeFuego|Bola de fuego]]"
```

La propiedad se considera **generada**: no debe editarse manualmente. Cada
ejecución del script la recalcula por completo.

## Catálogo inicial

El experimento usa como conceptos enlazables:

- las 12 clases principales;
- todos los animales salvo su `*-Index.md`;
- todos los conjuros salvo su `*-Index.md`;
- las notas de `Dotes/` salvo su índice;
- las notas de `Equipo/` salvo su índice;
- los monstruos de `MonstruosDeLaAALaZ/` salvo su índice;
- las notas de `ObjetosMagicos/` salvo su índice.

Las carpetas `(Alt)` no forman parte del catálogo.

> Nota: en la estructura actual, Dotes y Equipo no tienen una nota por cada
> dote u objeto individual. El experimento enlaza la granularidad que realmente
> existe en el repositorio.

## Qué notas se analizan

Se recorren todas las notas `.md` de `ES/`, excepto:

- carpetas `(Alt)`;
- archivos `*-Index.md`.

Estas exclusiones evitan convertir índices ya enlazados en hubs artificiales.

## Cómo se detecta una relación

1. El nombre canónico de cada concepto se toma del primer encabezado H1 de su
   nota, no del nombre físico del archivo.
2. La búsqueda ignora mayúsculas/minúsculas.
3. Se exige coincidencia del título completo con límites de palabra.
4. No se generan autoenlaces.
5. Si dos notas tienen exactamente el mismo título, el título ambiguo se omite
   y se informa por stderr.
6. Los enlaces se guardan con ruta relativa a la raíz de una bóveda formada por
   el contenido de `ES/`, por ejemplo:
   `[[Animales/AguilaGigante|Águila gigante]]`.

El script no elimina acentos durante la comparación: es una decisión
conservadora para reducir falsos positivos.

## Uso

Primero conviene inspeccionar el resultado sin escribir:

```bash
python scripts/generar_wikilinks_es.py --dry-run --verbose
```

Para aplicar los cambios en la rama:

```bash
python scripts/generar_wikilinks_es.py
```

Volver a ejecutarlo es seguro: `wikilinks_auto` se sustituye de forma
determinista en lugar de acumular enlaces.

## Criterio del experimento

La rama debe permitir responder dos preguntas antes de llevar esta idea más
lejos:

1. ¿El grafo resultante aporta navegación útil o genera demasiado ruido?
2. ¿Qué títulos concretos producen demasiadas relaciones y necesitan una
   exclusión o una regla más estricta?

Si el enfoque funciona, el siguiente paso natural es convertir el catálogo y
las exclusiones en configuración explícita y extender el mismo mecanismo a EN.
