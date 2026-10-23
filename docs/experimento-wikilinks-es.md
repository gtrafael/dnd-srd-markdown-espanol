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


## Resultado de la primera ejecución

La primera generación completa sobre ES produjo:

- 977 notas candidatas en las familias configuradas;
- 971 conceptos utilizables de forma inequívoca;
- 3 títulos ambiguos, cada uno presente en dos notas:
  - `Druida`: clase y monstruo;
  - `Mago`: clase y monstruo;
  - `Objetos mágicos`: nota de Equipo y nota de ObjetosMagicos;
- 1028 notas de contenido analizadas;
- 877 notas con alguna relación generada;
- 4031 wikilinks automáticos.

El workflow valida además que la generación no modifica el cuerpo Markdown de
ninguna nota.

### Hallazgo principal: ambigüedad semántica

La coincidencia textual demuestra que la infraestructura funciona, pero también
que "el mismo texto" no siempre significa "el mismo concepto".

Ejemplos observados:

- en `Clases/Barbaro.md`, "paquete de explorador" puede generar un enlace a
  la clase `Explorador`;
- "escudo" puede referirse al equipo y no al conjuro `Escudo`;
- "guardia" puede ser un sustantivo común y no el perfil de monstruo
  `Guardia`;
- en cambio, `Conjuros/BolaDeFuego.md` relaciona de forma razonable
  `Hechicero` y `Murciélago`.

Por tanto, esta primera versión debe considerarse deliberadamente un
**baseline léxico**, no una versión lista para fusionar en `main`.

El siguiente experimento debería medir qué estrategia reduce más el ruido sin
perder relaciones útiles. Algunas opciones son: exigir contexto según categoría,
mantener una lista de títulos inherentemente ambiguos, o aplicar reglas más
estrictas a nombres cortos y genéricos.


## v2: relaciones por entidad

La v2 abandona deliberadamente los capítulos o notas contenedoras como destinos
del grafo. Una relación automática solo puede apuntar a una entidad concreta.

### Entidades con nota propia

Se reutilizan directamente las notas reales de:

- clases;
- animales;
- conjuros;
- monstruos;
- objetos mágicos.

El catálogo se construye por estructura, no por el simple hecho de que exista
un archivo Markdown. Así, notas como Conjuros.md, Armas.md o los índices no
pueden convertirse accidentalmente en conceptos enlazables.

### Dotes y equipo

Dotes y Equipo contienen muchas entidades dentro de una misma nota. Como el
grafo de Obsidian trabaja a nivel de nota, la v2 genera nodos auxiliares en:

- ES/_Entidades/Dotes/
- ES/_Entidades/Equipo/

Son notas generadas que contienen solo frontmatter. No duplican el contenido
del SRD. Guardan el nombre de la entidad y un enlace source a la sección
original. Esto permite que Alerta, Honda, Escudo, Linterna de ojo de buey,
etc. sean nodos independientes del grafo sin convertir DotesGenerales.md o
Armas.md en hubs artificiales.

### Desambiguación determinista

El buscador ordena los nombres por longitud y consume primero la coincidencia
más larga. Por ejemplo, Paquete de explorador se reconoce antes que Explorador,
por lo que esa frase no genera además una relación con la clase Explorador.

Cuando un mismo nombre representa varias entidades legítimas, se conservan
todos los destinos. Por ejemplo, Druida y Mago pueden apuntar tanto a la clase
como al perfil de monstruo correspondiente.

El workflow verifica además dos invariantes: ningún cuerpo Markdown existente
puede cambiar y no pueden reaparecer destinos contenedores prohibidos.
