# AGENTS.md

Instructions for AI coding agents working on this repository.

## Project identity

This is a **Spanish-first** D&D 5.5E SRD v5.2.1 repository. All content is Markdown formatted as an Obsidian vault. Spanish translation was generated from the official PDF `SP_SRD_CC_v5.2.1.pdf` (stored at `src/SP_SRD_CC_v5.2.1.md`). English files come from the [DND.SRD.Wiki](https://github.com/OldManUmby/DND.SRD.Wiki) project upgraded to 5.2.1.

- **1220+ Spanish files** across all SRD categories
- **997+ English files** with full cross-referencing
- No build system, no package manager, no tests — this is a content repository

## Root layout

```
├── ES/                              # Spanish content (primary)
│   ├── Espanol.md                   #   Entry point / main index
│   ├── ComoJugar/                   #   Core rules (10 files)
│   ├── Clases/                      #   12 classes + index (13 files)
│   ├── CreacionDePersonajes/        #   Character creation (7 files)
│   ├── OrigenesDePersonaje/         #   Character origins (3 files)
│   ├── Dotes/                       #   Feats (6 files)
│   ├── Equipo/                      #   Equipment (17 files)
│   ├── Conjuros/                    #   342 spells + index
│   ├── Conjuros (Alt)/              #   Spells grouped A–Z (8 files)
│   ├── GlosarioDeReglas/            #   Rules glossary by letter (21 files)
│   ├── HerramientasDelJuego/        #   DM tools (9 files)
│   ├── ObjetosMagicos/              #   262 magic items + index
│   ├── ObjetosMagicos (Alt)/        #   Items grouped A–Z (8 files)
│   ├── Monstruos/                   #   Monster rules (1 unified doc)
│   ├── MonstruosDeLaAALaZ/          #   236 individual monsters + index
│   ├── MonstruosDeLaAALaZ (Alt)/    #   Monsters grouped A–Z (8 files)
│   ├── Animales/                    #   96 animals + index
│   └── Animales (Alt)/              #   Animals grouped A–Z (7 files)
├── EN/                              # English content (secondary)
│   ├── English.md                   #   Entry point
│   ├── Gameplay/                    #   Core rules (4 files)
│   ├── Species/                     #   Species (10 files)
│   ├── Classes/                     #   12 classes + index (13 files)
│   ├── Characterizations/           #   Backgrounds, feats, etc. (6 files)
│   ├── Equipment/                   #   Equipment (11 files)
│   ├── Spells/                      #   340 spells + index
│   ├── Spells (Alt)/                #   Grouped A–Z (23 files)
│   ├── Monsters/                    #   235 monsters + index
│   ├── Monsters (Alt)/              #   Grouped A–Z (26 files)
│   ├── Animals/                     #   95 animals + index
│   ├── Animals (Alt)/               #   Grouped A–Z (20 files)
│   ├── Treasure/                    #   173 magic items + index
│   ├── Treasure (Alt)/              #   Grouped A–Z (23 files)
│   ├── Gamemastering/               #   DM tools (11 files)
│   └── Rules Glossary/              #   Rules glossary (2 files)
├── src/                             # Source files
│   ├── SP_SRD_CC_V5.2.1.md          #   Monolithic Spanish source (~1.8 MB)
│   └── SP_SRD_CC_V5.2.1_index.json  #   Section index
├── scripts/                         # Utility scripts
│   └── crlf_to_lf.ps1               #   CRLF → LF converter
├── .obsidian/                       # Obsidian vault config (auto-generated)
├── SKILL.md                         # LLM skill descriptor for lookups
├── README.md                        # Human-facing project readme
├── CHANGELOG.md
├── Legal.md
└── License.md                       # CC-BY-4.0 full text
```

## Critical conventions

### File naming

- **ES files**: Spanish names, **no spaces** — `BolaDeFuego.md`, `DragonRojoAdulto.md`, `BastonDePoder.md`
- **EN files**: English names with **spaces** — `Fireball.md`, `Adult Red Dragon.md`, `Staff of Power.md`
- **Index files**: `{Category}-Index.md` in ES (e.g. `Conjuros-Index.md`), `{Category}.md` in EN (e.g. `Spells.md`)
- **Entry points**: `ES/Espanol.md`, `EN/English.md`

### Frontmatter (YAML, every file)

**ES files:**
```yaml
---
aliases: ["Spanish Name", "English Name"]
tags: [srd, espanol, tag_{category}]
related_en: "[[EN-Dir/EN-File|Display (EN)]]"
---
```

**EN files:**
```yaml
---
aliases: ["English Name", "Spanish Name"]
tags: [srd, english, tag_{category}]
related_es: "[[ES-Dir/ES-File|Display (Español)]]"
---
```

**Special cases:**
- Files with no equivalent in the other language get `sin-equivalente` tag and no `related_en`/`related_es`
- Category tags: `tag_clases`, `tag_conjuros`, `tag_monstruos`, `tag_animales`, `tag_equipo`, `tag_dotes`, `tag_origenes`, `tag_tesoro`, `tag_comojugar`, `tag_creaciondepersonajes`, `tag_glosariodereglas`, `tag_herramientasdeljuego`

### Wikilinks

All internal links use Obsidian wikilink syntax. Never use Markdown `[text](path.md)` for internal content.

```markdown
[[Conjuros/BolaDeFuego|Bola de fuego]]   # Link with custom display text
[[Clases/Barbaro]]                        # Direct link (display = filename)
```

Markdown `[text](url)` links are only for external URLs.

### Markup differences between ES and EN

| Feature | EN | ES |
|---|---|---|
| Tables | Markdown pipe tables | HTML `<table>` tags |
| Distances | Feet (ft) | Meters (m), 1 square = 1.5 m |
| Units | Imperial | Metric |
| Monster docs | Rules embedded in each file | Separate rules doc (`Monstruos/Monstruos.md`) + individual stat blocks |
| Cross-reference links | Via frontmatter `related_es` | Via frontmatter `related_en` |

ES files use HTML tables intentionally — this is the format from the official Spanish PDF and should be preserved.

### Consolidated (Alt) directories

The `(Alt)` directories group content alphabetically for browsing. Each file covers a letter range:

- `Conjuros (Alt)/Conjuros A-C.md` — all spells starting with A through C
- `MonstruosDeLaAALaZ (Alt)/MonstruosDeLaAALaZ D-F.md` — monsters D through F
- Same pattern for `ObjetosMagicos (Alt)/` and `Animales (Alt)/`

When making bulk changes, update both the individual file and its corresponding (Alt) entry.

## Editing rules

### When adding or modifying a file

1. **Every ES file must have**: `aliases`, `tags`, `related_en` in frontmatter
2. **Every EN file must have**: `aliases`, `tags`, `related_es` in frontmatter  
3. **Wikilinks must match filenames exactly** — Obsidian treats `[[file]]` as case-insensitive but the path must resolve
4. **Keep HTML tables in ES files** — don't convert them to Markdown tables
5. **Keep Imperial in EN, Metric in ES** — don't convert units across languages
6. **No emojis** anywhere unless the user explicitly requests them
7. **No comments** in Markdown files — the frontmatter is self-documenting

### When renaming or moving files

1. Update all wikilinks that point to the renamed file
2. Update the category's `-Index.md` file
3. Update any `(Alt)` files that include the entry
4. Update `related_en`/`related_es` in the counterpart file
5. Update `aliases` if the previous name was used as an alias

### When creating new content

1. Follow existing naming conventions (no spaces in ES, spaces in EN)
2. Copy frontmatter structure from a similar existing file
3. Add the file to the category index (`-Index.md`)
4. Add the file to the appropriate `(Alt)` consolidated file
5. Add bidirectional cross-reference if a counterpart exists

## How to find things

```
# Spanish content
ES/Conjuros/BolaDeFuego.md              # exact spell
ES/Conjuros/*Fuego*.md                  # partial name
ES/MonstruosDeLaAALaZ/*Dragon*.md       # partial monster name
ES/GlosarioDeReglas/LetraC.md           # rules glossary, letter C

# English content  
EN/Spells/Fireball.md                   # exact spell
EN/Monsters/*Dragon*.md                 # partial monster name
EN/Rules Glossary/Rules Glossary.md     # full rules glossary

# Cross-language: follow frontmatter related_en/related_es
```

For rules lookup, check the glossary first (`ES/GlosarioDeReglas/` or `EN/Rules Glossary/`). For spell lists per class, read the class file directly.

## Things to never do

- **Don't convert HTML tables to Markdown** in ES files
- **Don't convert Metric to Imperial** in ES files (or vice versa)
- **Don't remove frontmatter** from any file
- **Don't replace wikilinks with Markdown links** for internal references
- **Don't add `## Related Links` or `## Enlaces relacionados` sections** — cross-referencing is frontmatter-only
- **Don't create new top-level directories** without discussion
- **Don't rename ES directories** — the names match the official Spanish PDF structure
- **Don't run `crlf_to_lf.ps1`** unless there's a known line-ending issue
- **Don't add build tools, formatters, or linters** without discussion

## Git workflow

- The source file `src/SP_SRD_CC_V5.2.1.md` is 1.8 MB — avoid adding it to context unnecessarily

## License

All SRD content is [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/). See `License.md` for full text and `Legal.md` for attribution. The `logo.png` is used under Wizards of the Coast's Fan Site Kit.
