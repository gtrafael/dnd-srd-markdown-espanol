# Experimento de wikilinks automáticos ES-EN

Esta rama prueba una capa determinista de relaciones para Obsidian sin modificar
el cuerpo Markdown de las notas. La misma lógica se aplica a las bóvedas ES y EN.

## Principio de diseño

Solo puede ser destino de wikilinks_auto una entidad que ya exista como nota
física en la bóveda del mismo idioma.

El generador no crea notas auxiliares, no divide tablas y no altera la
granularidad del repositorio. Los enlaces automáticos se mantienen dentro de ES
o dentro de EN. Las relaciones bilingües explícitas siguen usando related_en y
related_es.

## Catálogo dinámico

El catálogo se descubre por estructura y contenido, no mediante listas fijas.

Se reconocen:

- clases/classes por su estructura de clase;
- animales/animals y monstruos/monsters por sus bloques de estadísticas;
- conjuros/spells por sus cuatro campos de lanzamiento;
- dotes/feats si existe una nota física individual con firma de dote;
- objetos mágicos/magic items por su estructura y rareza.

Los índices, carpetas (Alt) y notas contenedoras no son destinos.

EN usa encabezados de distintos niveles para entidades (por ejemplo ### para
spells y magic items y ## para animals/monsters). El generador usa el primer
encabezado de una nota validada como nombre canónico, por lo que no depende de
que todas las entidades sean H1.

## Longest match y bloqueadores

Los nombres se ordenan de mayor a menor longitud. Además, encabezados
estructurales pueden actuar como bloqueadores sin convertirse en nodos.

Ejemplos:

- ES: "paquete de explorador" bloquea Explorador dentro de esa frase;
- EN: el mismo mecanismo se aplica cuando una expresión estructural contiene
  literalmente el nombre de otra entidad. No se fuerza una equivalencia
  semántica entre "Explorer" y "Ranger", porque son palabras distintas.

Los prefijos mecánicos "Nivel N:" y "Level N:" se eliminan al crear variantes de
bloqueo, igual que sufijos entre paréntesis como precios.

## Conjuros/spells de una palabra

Los nombres de una palabra son especialmente ambiguos con vocabulario ordinario.

Para destinos de tipo spell/conjuro cuyo título es una sola palabra:

- en tablas, la coincidencia solo es válida si cae en una columna que contiene
  Conjuro/Truco o Spell/Cantrip;
- en prosa, necesita contexto cercano explícito de lanzamiento, preparación o
  aprendizaje de conjuros.

Ejemplos:

- "el águila puede volar" no enlaza Volar;
- "the eagle can fly" no enlaza Fly;
- "puedes lanzar el conjuro volar" sí enlaza Volar;
- "you can cast the Fly spell" sí enlaza Fly;
- Adivinación/Divination en una columna Escuela/School no enlaza el conjuro;
- Ralentizar/Slow en una columna Maestría/Mastery no enlaza el conjuro.

No se aplica sensibilidad global a mayúsculas/minúsculas.

## Homónimos

Si dos notas físicas distintas comparten exactamente el mismo nombre, se
conservan ambos destinos. Esto permite representar casos legítimos como Mago
clase y Mago monstruo sin forzar una desambiguación artificial.

## Uso

Procesar ambos idiomas:

python scripts/generar_wikilinks.py

Simulación:

python scripts/generar_wikilinks.py --dry-run --verbose

Solo un idioma:

python scripts/generar_wikilinks.py --lang ES
python scripts/generar_wikilinks.py --lang EN

Cada ejecución recalcula por completo wikilinks_auto. El cuerpo Markdown no se
modifica.

## Validaciones automáticas

El workflow comprueba:

- sintaxis del generador;
- generación ES y EN;
- longest-match y bloqueadores en ambos idiomas;
- protección de conjuros/spells de una palabra en ambos idiomas;
- ausencia de carpetas de entidades auxiliares;
- preservación exacta de los cuerpos Markdown;
- idempotencia de una segunda ejecución.

## Historia

La v1 trataba como entidades demasiadas notas contenedoras.

La v2 creó nodos auxiliares para elementos embebidos en tablas y secciones. Se
descartó porque alteraba la estructura y el número de notas.

La v3 volvió a reflejar estrictamente la granularidad física real del
repositorio e introdujo bloqueadores estructurales.

La v3.1 añadió contexto para conjuros de una sola palabra.

La siguiente evolución extiende la misma arquitectura a EN sin duplicar el
motor ni introducir reglas paralelas.


## Resultado bilingüe estable

Tras la primera regeneración completa ES-EN:

- ES:
  - 939 entidades;
  - 937 títulos únicos;
  - 194 bloqueadores;
  - 2 homónimos reales: Druida y Mago;
  - 3655 wikilinks.
- EN:
  - 939 entidades;
  - 938 títulos únicos;
  - 200 bloqueadores;
  - 1 homónimo real: Druid clase y Druid monstruo;
  - 3247 wikilinks.

Distribución EN:

- 12 classes;
- 95 animals;
- 339 spells;
- 235 monsters;
- 258 magic items.

La primera ejecución añadió o actualizó wikilinks_auto en 699 notas EN. Una
segunda ejecución consecutiva produjo 0 cambios, por lo que la generación
bilingüe es idempotente.

## Relaciones spell-clase

Las clases declaradas en la cabecera de cada spell se detectan como entidades
normales del mismo idioma. Por ejemplo:

- Bola de fuego enlaza a Hechicero y Mago;
- Fireball enlaza a Sorcerer y Wizard.

El workflow contiene una prueba explícita para conservar estas relaciones en
ambos idiomas.


## Auditoría de simetría ES-EN

La estructura física de las familias de entidad es simétrica:

- 12 clases/classes;
- 95 animales/animals;
- 339 conjuros/spells;
- 235 monstruos/monsters;
- 258 objetos mágicos/magic items.

También existen 1010 notas analizables en cada idioma.

La diferencia inicial de 861 entidades ES frente a 939 EN no procedía del
corpus. El detector español de objetos mágicos dependía de palabras de rareza
del descriptor y omitía formas femeninas y entradas de rareza variable. La
carpeta canónica `ObjetosMagicos/ObjetosMagicosDeLaAALaZ` ya contiene una nota
física por entidad, por lo que ahora se usa esa estructura como fuente de
verdad, igual que `Magic Items/Magic Items A-Z` en EN.

Tras el cambio ambos idiomas contienen 939 entidades. La diferencia de títulos
únicos (937 ES frente a 938 EN) es legítima: ES tiene dos homónimos
clase/monstruo (Druida y Mago), mientras EN solo tiene Druid; Wizard y Mage son
nombres distintos.

El workflow comprueba dinámicamente que todos los objetos mágicos físicos de las
carpetas canónicas sean detectados, sin fijar el número 258 en el código.

## Pendientes semánticos para la decisión final del grafo

La auditoría ha identificado relaciones léxicamente válidas o ambiguas cuya
conveniencia depende de qué queramos que signifique una arista. No se han
corregido todavía:

- Guard/Guardia puede aparecer por expresiones ordinarias como "drop their
  guard" o "bajar/montar guardia";
- Spy puede aparecer por el verbo inglés "to spy";
- el filtro contextual de spells/conjuros de una palabra todavía puede aceptar
  Creation/Creación o Shield/Escudo cuando una referencia ordinaria queda cerca
  de las palabras spell/conjuro en una frase larga;
- Fireball/Bola de fuego enlaza Bat/Murciélago por el componente material
  "bat guano/guano de murciélago", una mención literal cuya utilidad en el grafo
  depende de la semántica que finalmente adoptemos.

Estos casos se mantienen sin cambios hasta decidir si el grafo representa
menciones textuales o relaciones reglísticas significativas.
