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


## Resultado estable de la v3

La primera regeneración completa de la v3 produjo:

- 861 entidades físicas reconocidas;
- 859 nombres distintos;
- 2 homónimos reales: Druida y Mago;
- 1027 notas analizadas;
- 4288 wikilinks automáticos;
- 418 notas cuyo frontmatter cambió respecto a la v2;
- 0 cambios en una segunda ejecución consecutiva.

Distribución del catálogo:

- 95 animales;
- 12 clases;
- 339 conjuros;
- 235 monstruos;
- 180 objetos mágicos.

Actualmente no entra ninguna dote como destino porque el repositorio no contiene
notas físicas individuales de dote que cumplan la firma de entidad definida por
la v3.

## Mayúsculas y minúsculas

Se evaluó usar la capitalización como filtro de desambiguación.

Ayuda en algunos falsos positivos. Por ejemplo, "terror" como sustantivo común
no debería enlazar necesariamente al conjuro Terror.

Sin embargo no puede aplicarse globalmente porque el SRD contiene referencias
válidas en minúsculas, como los nombres de clase dentro de las fichas de
conjuros ("hechicero, mago") y nombres de conjuros usados en prosa.

Además, varios falsos positivos sobreviven aunque respetemos mayúsculas:
"Resistencia al daño", "Salto instintivo" o la propiedad de maestría
"Ralentizar" aparecen capitalizados.

Por tanto, la v3 mantiene por ahora la comparación sin distinguir mayúsculas y
minúsculas. Cualquier refinamiento posterior debe ser más conservador y medirse
sobre ejemplos reales antes de incorporarse.


## V3.1: conjuros de una palabra

La auditoría de la v3 mostró que la mayor parte del ruido restante procedía de
conjuros cuyo nombre también es vocabulario ordinario: Luz, Escudo, Resistencia,
Dormir, Volar, Terror, Ralentizar, Adivinación, etc.

No se aplica sensibilidad global a mayúsculas/minúsculas, porque el SRD contiene
muchas referencias válidas en minúscula a clases, monstruos, animales y
conjuros.

La v3.1 añade una regla únicamente para destinos de tipo conjuro cuyo título
consta de una sola palabra:

- en tablas, la coincidencia solo es válida si cae en una columna cuyo
  encabezado contiene "Conjuro" o "Truco";
- en prosa, la coincidencia necesita contexto cercano explícito de conjuro,
  como conjuro/conjuros, truco/trucos, lanzar, preparar o aprender.

Los conjuros de varias palabras y las demás categorías conservan el
comportamiento anterior.

Ejemplos:

- "el águila puede volar 18 m" no enlaza al conjuro Volar;
- "puedes lanzar el conjuro volar" sí enlaza Volar;
- Adivinación en la columna Escuela no enlaza el conjuro Adivinación;
- Adivinación en la columna Conjuro sí lo enlaza;
- Ralentizar en una columna Maestría no enlaza el conjuro Ralentizar.

El workflow contiene pruebas de regresión para estos casos.

### Resultado

Tras aplicar esta protección, el grafo pasa de 4234 a 3639 wikilinks
automáticos. La reducción es de 595 relaciones. La revisión de muestras confirma
que desaparecen falsos positivos masivos como Volar en velocidades de animales,
Luz en iluminación, Escudo como equipo, Ralentizar como maestría y Adivinación
como escuela mágica, mientras se conservan las apariciones dentro de listas de
conjuros y en contexto explícito de lanzamiento.

La generación sigue siendo idempotente y el workflow completo termina
correctamente.
