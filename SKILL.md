---
name: dnd-srd-spanish
description: Reference the D&D 5.5E SRD v5.2.1 in Spanish and English. Use for D&D rules, spells, monsters, classes, equipment, magic items, and game mechanics. Spanish-first with EN mirror. Designed as an Obsidian vault with wikilinks, tags, and cross-references.
user-invocable: true
metadata:
  version: 5.2.1
---

# D&D 5.5E SRD — Spanish Edition

Conversión completa del SRD 5.2.1 a Markdown. El proyecto es **Spanish-first**: `ES/` contiene la traducción oficial generada desde el PDF en español `SP_SRD_CC_v5.2.1.pdf`. `EN/` es la versión original en inglés (basada en el trabajo de Old Man Umby y GaZmagik).

Cada archivo en español tiene un `related_en` que enlaza a su equivalente en inglés, y viceversa (`related_es`). El proyecto está diseñado como bóveda de Obsidian: todos los enlaces internos son wikilinks (`[[ ]]`) y cada archivo incluye frontmatter YAML con aliases y tags.

Responde siempre en el idioma en que te hable el usuario. Para consultas en español, busca en `ES/`; para consultas en inglés, busca en `EN/`. Si el usuario mezcla idiomas, prioriza el español.

## Puntos de entrada

| Archivo | Propósito |
|---|---|
| `ES/Espanol.md` | Índice principal en español — enlaza todos los índices de categoría |
| `EN/English.md` | Main English index — links all category indexes |

## Estructura — Español (`ES/`)

Cada categoría tiene un archivo `-Index.md` que lista todos los documentos individuales. Los índices son la forma más rápida de navegar por categoría.

### Reglas y creación de personaje

| Directorio | Archivos | Contenido |
|---|---|---|
| `ComoJugar/` | 9 + index | Reglas básicas: acciones, combate, competencia, daño/curación, exploración, interacciones sociales, pruebas con D20, las seis características, ritmo de juego |
| `CreacionDePersonajes/` | 6 + index | Crear personaje, progresión de niveles, multiclase, bagatelas, empezar en niveles superiores, hojas de personaje |
| `OrigenesDePersonaje/` | 2 + index | Orígenes de personaje (trasfondos) |
| `Dotes/` | 5 + index | Dotes (Origin, General, Fighting Style, Epic Boon) |
| `GlosarioDeReglas/` | 20 + index | Definiciones alfabéticas de todos los términos, condiciones y reglas |

### Clases

| Directorio | Archivos | Contenido |
|---|---|---|
| `Clases/` | 12 + index | Bárbaro, Bardo, Brujo, Clérigo, Druida, Explorador, Guerrero, Hechicero, Mago, Monje, Paladín, Pícaro — cada archivo incluye tabla de rasgos, subclases y lista de conjuros |

### Equipo

| Directorio | Archivos | Contenido |
|---|---|---|
| `Equipo/` | 16 + index | Armas, armaduras, propiedades de maestría, herramientas, monedas, gastos, monturas/vehículos, equipo de aventureros, comida/bebida/alojamiento, asalariados, fabricar objetos, elaborar pociones, elaborar pergaminos, lanzamiento de conjuros (servicios) |

### Conjuros

| Directorio | Archivos | Contenido |
|---|---|---|
| `Conjuros/` | 343 + index | Un archivo por conjuro (ej. `Bola de Fuego.md`, `Abrir.md`). Cada uno incluye: nivel, escuela, clases, tiempo de lanzamiento, alcance, componentes, duración, descripción |
| `Conjuros (Alt)/` | 8 | Los mismos conjuros agrupados por letra: `Conjuros A-C.md` … `Conjuros V-Z.md` |

### Monstruos

| Directorio | Archivos | Contenido |
|---|---|---|
| `Monstruos/Monstruos.md` | 1 | Documento unificado con las reglas de perfiles de monstruo (partes de un perfil, tipos, tamaños, alineamientos) |
| `MonstruosDeLaAALaZ/` | 236 + index | Un archivo por monstruo (ej. `Aboleth.md`, `Dragon Rojo Adulto.md`). Incluye: tipo/tamaño/alineamiento, CA, Iniciativa, PG, velocidad, características, VD, rasgos, acciones, acciones adicionales, reacciones, acciones legendarias |
| `MonstruosDeLaAALaZ (Alt)/` | 8 | Agrupados por letra: `MonstruosDeLaAALaZ A-C.md` … `MonstruosDeLaAALaZ V-Z.md` |

**Convenciones de nombres de monstruos:**
- Estándar: `{Nombre}.md` (ej. `Aboleth.md`, `Gigante de las Colinas.md`)
- Dragones: `{Edad} {Color}.md` (ej. `Adulto Rojo.md`, `Antiguo Dorado.md`)
- Dragones jóvenes: `{Color} Joven.md` (ej. `Rojo Joven.md`)
- PNJs mezclados alfabéticamente: `Archimago.md`, `Guardia.md`, `Espia.md`

### Animales

| Directorio | Archivos | Contenido |
|---|---|---|
| `Animales/` | 96 + index | Un archivo por animal (ej. `Lobo Terrible.md`, `Alosaurio.md`). Mismo formato de perfil que los monstruos |
| `Animales (Alt)/` | 7 | Agrupados: `Animales A-C.md` … `Animales S-U.md` |

### Objetos mágicos

| Directorio | Archivos | Contenido |
|---|---|---|
| `ObjetosMagicos/` | 262 + index | Un archivo por objeto (ej. `Baston de Poder.md`, `Espada Vorpal.md`). Incluye rareza, sintonización y descripción |
| `ObjetosMagicos (Alt)/` | 8 | Agrupados: `ObjetosMagicos A-C.md` … `ObjetosMagicos V-Z.md` |

### Herramientas del juego (para el DM)

| Directorio | Archivos | Contenido |
|---|---|---|
| `HerramientasDelJuego/` | 8 + index | Crear un trasfondo, efectos ambientales, encuentros de combate, maldiciones y enfermedades mágicas, miedo y estrés psicológico, ritmo de viaje, trampas, veneno |

## Estructura — Inglés (`EN/`)

El directorio `EN/` contiene la versión original en inglés. Usa estos archivos cuando el usuario pregunte en inglés.

| Directorio EN | Equivalente ES | Archivos | Contenido |
|---|---|---|---|
| `Gameplay/` | `ComoJugar/` | 4 | Abilities, combat, adventuring, damage/healing |
| `Species/` | _(integrado en OrigenesDePersonaje)_ | 10 | Dragonborn, Dwarf, Elf, Gnome, Goliath, Halfling, Human, Orc, Tiefling, index |
| `Classes/` | `Clases/` | 13 | Barbarian, Bard, Cleric, Druid, Fighter, Monk, Paladin, Ranger, Rogue, Sorcerer, Warlock, Wizard, index |
| `Characterizations/` | `CreacionDePersonajes/` + `Dotes/` | 6 | Backgrounds, Feats, Languages, Multiclassing, Trinkets, index |
| `Equipment/` | `Equipo/` | 11 | Weapons, Armor, Tools, Gear, Coinage, Expenses, Transportation, Crafting, Selling Treasure, Spellcasting services, index |
| `Spells/` | `Conjuros/` | 341 + index | One file per spell |
| `Spells (Alt)/` | `Conjuros (Alt)/` | 23 | Grouped A–Z |
| `Monsters/` | `MonstruosDeLaAALaZ/` | 237 + index | One file per monster (rules embedded, no separate doc) |
| `Monsters (Alt)/` | `MonstruosDeLaAALaZ (Alt)/` | 26 | Grouped A–Z |
| `Animals/` | `Animales/` | 96 + index | One file per animal |
| `Animals (Alt)/` | `Animales (Alt)/` | 20 | Grouped A–Z |
| `Treasure/` | `ObjetosMagicos/` | 174 + index | One file per magic item |
| `Treasure (Alt)/` | `ObjetosMagicos (Alt)/` | 23 | Grouped A–Z |
| `Gamemastering/` | `HerramientasDelJuego/` | 11 | Travel, Curses, Magical Contagions, Environmental Effects, Fear and Mental Stress, Poisons, Traps, Combat Encounters, Creating a Background, NPCs, index |
| `Rules Glossary/` | `GlosarioDeReglas/` | 2 | Rules glossary + index |

## Formato de archivos y convenciones

### Frontmatter

Cada archivo individual incluye frontmatter YAML con tres campos:

```yaml
---
aliases: ["Nombre en español", "English Name"]  # nombres alternativos para búsqueda
tags: [srd, espanol, tag_categoria]              # srd + idioma + categoría
related_en: "[[path/File|Display]]"               # enlace al equivalente en el otro idioma
---
```

Categorías de tags: `tag_conjuros`, `tag_monstruos`, `tag_clases`, `tag_equipo`, `tag_tesoro`, `tag_animales`, `tag_dotes`, `tag_origenes`, etc.

Los archivos EN usan `tags: [srd, english, tag_...]` y `related_es` en lugar de `related_en`.

### Wikilinks

Todos los enlaces entre documentos internos usan sintaxis de wikilink de Obsidian:
- `[[Conjuros/Bola de Fuego|Bola de fuego]]` — enlace a nota con texto personalizado
- `[[Clases/Barbaro]]` — enlace directo (el display text es el nombre del archivo)

No se usan enlaces Markdown estándar `[text](url)` para contenido interno — solo para URLs externas.

### Archivos índice (`-Index.md`)

Cada categoría tiene un archivo `{Categoria}-Index.md` que contiene:
- Título de la categoría
- Conteo de archivos
- Lista de wikilinks a cada documento individual

Estos índices son la forma más rápida de navegar y descubrir el contenido de una categoría.

### Archivos agrupados (`(Alt)`)

Los directorios `(Alt)` contienen versiones consolidadas donde múltiples entradas comparten un mismo archivo, agrupadas por rango de letras (A-C, D-F, etc.). Útiles para búsquedas amplias o cuando necesitas ver varias entradas relacionadas a la vez.

## Cómo encontrar contenido

- **Por nombre exacto**: Lee el archivo directamente: `ES/Conjuros/Bola de Fuego.md`, `ES/MonstruosDeLaAALaZ/Aboleth.md`
- **Por nombre parcial**: Usa Glob con wildcard: `ES/Conjuros/*Bola*.md`, `ES/MonstruosDeLaAALaZ/*Dragon*.md`
- **Por palabra clave en contenido**: Usa Grep en el directorio relevante: busca "furioso" en `ES/Clases/`, "Exhaustion" en `EN/Rules Glossary/`
- **Para condiciones y términos de juego**: Revisa `ES/GlosarioDeReglas/` o `EN/Rules Glossary/`
- **Para listas de conjuros por clase**: Lee el archivo de la clase directamente (las listas de conjuros están dentro de cada clase)
- **Navegación general**: Empieza por `ES/Espanol.md` o `EN/English.md` y sigue los wikilinks
- **Prefiere los directorios individuales** para búsquedas precisas. Usa los directorios `(Alt)` cuando necesites explorar varias entradas a la vez
- **Comparaciones bilingües**: Sigue el campo `related_en`/`related_es` en el frontmatter de cualquier archivo para ir al equivalente en el otro idioma

## Licencia

Todo el contenido del SRD está publicado bajo [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/legalcode) (CC-BY-4.0). El SRD 5.2.1 es propiedad de Wizards of the Coast LLC, disponible en https://www.dndbeyond.com/srd.
