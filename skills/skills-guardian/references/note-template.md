# Evaluation note template

Save it as `<notes_dir>/note-<name>.md` (English) or `<notes_dir>/nota-<name>.md` (Spanish); run
`registry.py where` to see `notes_dir`. When several skills from the same repository are
evaluated together, one note can cover all of them. Write in the user's language and for the
user: if `profile.about` says they are not a developer, explain technical terms the first time
they appear. Sections can grow or shrink as needed.

```markdown
# Note: <name>, <what it is in a few words>

Date: <YYYY-MM-DD>. Reviewed `<owner/repo>` at commit `<short hash>` (<version if any>).

## 1. What it is
<Skill, plugin, MCP server or program. If it is not "just a skill", say so first.>

## 2. Trust
<Author, stars, license, activity, CVEs. If it is not clearly trustworthy: what was reviewed and
what was found in hooks, scripts, allowed-tools and network access.>

## 3. What it is for
<What it does, with a concrete example from the user's work.>

## 4. How it would affect your projects
| Project | Effect |
|---|---|
| <one row per project in profile.projects> | … |

### Risks and things to watch
<Over-triggering, clashes with other skills, privacy, telemetry, etc.>

## 5. Recommended install
<Location (full path), exactly which folders, what is left out (hooks, plugin) and why.
Proposed adjustments. How to uninstall.>

**Status: NOT INSTALLED (waiting for a decision).**

## 6. How to check that it works
<Requests that should trigger it and requests that should not.>
```

When it is installed, replace the status line with, for example:
`**Status: INSTALLED on <date>** (<location>, <unchanged | adjusted: …>; copy verified).`
When it is rejected: `**Status: REJECTED on <date>.**`

In Spanish the same sections are: Qué es, Confiabilidad, Para qué sirve, Cómo afectaría tus
proyectos, Instalación recomendada, Cómo comprobar que funciona; and the status lines are
`**Estado: NO INSTALADA (pendiente de decisión).**`, `**Estado: INSTALADA el <fecha>** (…)` and
`**Estado: DESCARTADA el <fecha>.**`
