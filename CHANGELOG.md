# Changelog

## [1.1.0] — 2026-05-13

### Reformateo y Limpieza automática, conversión tablas a Markdown

- **Reformateo y limpieza automática completa** del proyecto
- **Conversión de tablas HTML a Markdown** en archivos de estadísticas
  - Completar valores faltantes de CON y CAR en tablas de monstruos y animales
  - Actualizado [AGENTS.md](AGENTS.md) para reflejar el cambio a Markdown pipe tables

## [1.0.0] — 2026-05-12

### Spanish SRD — First complete release

Conversión completa del SRD 5.2.1 al español desde el PDF oficial `SP_SRD_CC_v5.2.1.pdf`, con enlaces bidireccionales a la versión original en inglés.

**1220 archivos en español** cubriendo todas las categorías del SRD:

- **Reglas**: Cómo jugar (9 archivos), creación de personajes (6), orígenes de personaje (2), dotes (5), glosario de reglas por letra (20)
- **Clases**: 12 clases con tabla de rasgos, subclases y listas de conjuros
- **Conjuros**: 342 conjuros individuales + agrupados A–Z (8)
- **Monstruos**: documento unificado de reglas + 236 monstruos individuales + agrupados A–Z (8)
- **Animales**: 96 animales + agrupados A–Z (7)
- **Objetos mágicos**: 262 objetos + agrupados A–Z (8)
- **Equipo**: 16 archivos (armas, armaduras, herramientas, monturas, fabricación, etc.)
- **Herramientas del juego**: 8 archivos (trampas, veneno, encuentros, efectos ambientales, etc.)

**997 archivos en inglés** actualizados al SRD 5.2.1:

- Contenido del proyecto [DND.SRD.Wiki](https://github.com/OldManUmby/DND.SRD.Wiki) por Old Man Umby, actualizado a 5.2.1 por GaZmagik
- 341 conjuros, 237 monstruos, 174 objetos mágicos, 96 animales + reglas completas

**Enlaces cruzados bilingües:**

- Cada archivo ES incluye `related_en` en el frontmatter apuntando a su equivalente en inglés
- Cada archivo EN incluye `related_es` en el frontmatter apuntando a su equivalente en español
- Aliases en ambos idiomas para búsqueda por nombre en inglés o español

**Diseñado para Obsidian:**

- Wikilinks `[[ ]]` funcionales entre todos los documentos
- Archivos índice (`-Index.md`) en cada categoría para navegación jerárquica
- Tags por categoría (`tag_conjuros`, `tag_monstruos`, etc.) para filtrado
- Punto de entrada: `ES/Espanol.md`

**Formato:**

- Tablas HTML en archivos ES (desde el PDF oficial)
- Tablas Markdown en archivos EN
- Distancias en metros (ES) y pies (EN)
