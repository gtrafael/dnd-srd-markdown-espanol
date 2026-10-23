# Experimento de wikilinks automáticos en ES

Esta rama prueba una capa determinista de relaciones para Obsidian sin modificar
el cuerpo Markdown de las notas.

## V3: principio de diseño

La v3 aplica una regla principal:

Solo puede ser destino de wikilinks_auto una entidad que ya exista como nota
física en la bóveda.

El generador no crea notas auxiliares, no divide tablas y no altera la
granularidad del repositorio. La carpeta experimental ES/_Entidades usada en la
v2 se elimina por completo.

## Qué se considera entidad

El catálogo se descubre dinámicamente a partir de la estructura y del contenido
de las notas, no mediante una lista fija de nombres.

Actualmente se reconocen:

- clases con estructura real de clase;
- animales con bloque de estadísticas;
- conjuros con tiempo de lanzamiento, alcance, componentes y duración;
- dotes si existe una nota física individual cuya descripción comienza como una dote;
- monstruos con bloque de estadísticas;
- objetos mágicos con descriptor de rareza.

Las notas de índice, las carpetas (Alt) y las notas contenedoras no son
destinos. Equipo no aporta hoy entidades al catálogo porque sus objetos viven
principalmente dentro de tablas o capítulos y no tienen notas físicas
individuales inequívocas.

Todo el contenido ES, salvo índices de navegación, puede seguir actuando como
fuente de relaciones.

## Coincidencias

Los nombres se ordenan de mayor a menor longitud.

Si existen las entidades Explorador y Paquete de explorador, la frase
"paquete de explorador" genera solo la segunda relación. El intervalo completo
se consume antes de poder reconocer "explorador" dentro de él.

En cambio, "El explorador lleva un paquete de explorador" genera las dos
relaciones porque son dos apariciones independientes.

Si dos notas físicas distintas comparten exactamente el mismo nombre, se
conservan ambos destinos. No se fuerza una desambiguación arbitraria.

## Frontmatter

La propiedad generada es wikilinks_auto. Cada ejecución la recalcula por
completo. El cuerpo Markdown no se modifica.

## Uso

Simulación:

python scripts/generar_wikilinks_es.py --dry-run --verbose

Aplicación:

python scripts/generar_wikilinks_es.py

El workflow comprueba sintaxis, preservación del cuerpo Markdown, ausencia de
ES/_Entidades e idempotencia de la generación.

## Historia del experimento

La v1 trataba como entidades demasiadas notas contenedoras.

La v2 creó nodos auxiliares para elementos embebidos en tablas y secciones.
Aunque permitía representar Honda, Alerta o Linterna como nodos del grafo,
alteraba la estructura y el número de notas de la bóveda.

La v3 descarta esa estrategia y hace que el grafo refleje estrictamente la
granularidad física real del repositorio.
