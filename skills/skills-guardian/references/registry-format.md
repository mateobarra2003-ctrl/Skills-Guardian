# Register format

The register is a JSON file (by default `~/.claude/skills-guardian/registry.json`). The page is
rebuilt from it with `registry.py update`, which refuses to touch the page if anything required
is missing. Text values are written in the user's language; keys are always in English.

## Top level

| Key | Meaning |
|---|---|
| `schema` | Always `1`. |
| `language` | `en` or `es`: the language of the page labels. |
| `locale` | Optional, for dates (for example `en-GB`, `es-AR`). Defaults to the language. |
| `title` | The page title. |
| `updated` | Set by `update`. |
| `html` | Where the page is written. Absolute, or relative to the register file. |
| `notes_dir` | Folder for the evaluation notes. Absolute, or relative to the register file. |
| `skill_dir` | Set by `update`: where Skills Guardian itself is installed. |
| `published_url` | Optional: where the page was published, to republish it at the same address. |
| `profile` | `about` (free text about the user) and `projects` (list of `{name, path, kind, private_data}`). |
| `locations` | Install locations: `{key: {label, path, title?, desc?}}`. `global` is `~/.claude/skills/`; add one per project that gets skills. |
| `preexisting` | Skill folders that existed before the register (not evaluated). |
| `chains` | Optional: `[{title, steps: [{skill \| label, note?}]}]`, skills meant to be used in sequence. |
| `entries` | One per evaluated item, installed or rejected. |

## Entries

| Key | Required | Meaning |
|---|---|---|
| `name` | always | Folder name of the skill (or the name of the plugin or program). |
| `kind` | always | `skill`, `plugin`, `mcp`, `hook` or `program`. |
| `status` | always | `installed` or `rejected`. |
| `date` | always | `YYYY-MM-DD`. |
| `source` | always | Author · repository @ commit or version. |
| `what` | always | One or two sentences on what it does. |
| `note` | always | File name of the evaluation note (in `notes_dir`), or a short description if there is none. |
| `summary` | installed (recommended for rejected) | At most 45 characters, shown in the index. |
| `location` | installed | A key of `locations` (`null` for rejected). |
| `triggers` | installed | When it activates. |
| `examples` | installed | 2 or 3 real requests, using the user's own projects. |
| `installed` | installed | List of `{part, purpose}`. For a skill, the `SKILL.md` part also has `elements`: `[{name, purpose}]`, 2 or more. |
| `left_out` | installed | List of texts: what the source had and was not installed, and why. |
| `not_triggered_by` | optional | A request that should **not** activate it. |
| `changes` | optional | Only if the content was adjusted. Marks the card as "Adjusted". |
| `extra` | optional | Extra paths (an environment, an output folder). |
| `uninstall_extra` | optional | Extra steps to uninstall (delete an environment, revert an exclude). |
| `reasons` | rejected | 2 or 3 concrete reasons. |

## Example of an installed entry

```json
{
  "name": "pdf-tables",
  "kind": "skill",
  "location": "reports",
  "status": "installed",
  "date": "2026-10-14",
  "source": "Jane Doe · janedoe/pdf-skills @ a1b2c3d",
  "summary": "Extract tables from PDF reports",
  "what": "Extracts tables from PDF reports into CSV files, page by page.",
  "triggers": "When I ask to pull a table out of a PDF.",
  "examples": [
    "Extract the income statement table from annual-report-2025.pdf.",
    "Turn every table in the Q3 report into CSV files."
  ],
  "not_triggered_by": "Summarize this PDF (no tables involved).",
  "changes": "Uses the isolated environment ~/.venvs/pdf; never installs packages",
  "installed": [
    {
      "part": "SKILL.md (adjusted)",
      "purpose": "The steps to find, extract and check tables.",
      "elements": [
        {"name": "Local setup (added)", "purpose": "Use the isolated environment; never install packages."},
        {"name": "Step 1 · Find the tables", "purpose": "Detects which pages contain tables."},
        {"name": "Step 2 · Extract", "purpose": "Converts each table to CSV and checks the totals."}
      ]
    },
    {"part": "references/edge-cases.md", "purpose": "How to handle merged cells and multi-page tables."},
    {"part": "~/.venvs/pdf (outside synced folders)", "purpose": "Python with pdfplumber 0.11.4, pinned."}
  ],
  "left_out": [
    "The other 12 skills of the repository (forms, signatures, OCR): not needed.",
    "Its hook that ran on every message to watch for PDFs."
  ],
  "uninstall_extra": "Also delete ~/.venvs/pdf if no other skill uses it.",
  "note": "note-pdf-tables.md"
}
```

## Example of a rejected entry

```json
{
  "name": "free-tokens-proxy",
  "kind": "program",
  "location": null,
  "status": "rejected",
  "date": "2026-10-14",
  "source": "someone · free-tokens-proxy",
  "summary": "Proxy that reuses the subscription",
  "what": "A local proxy that routes Claude's requests through third-party providers.",
  "reasons": [
    "It holds every API key and reads every prompt.",
    "Reusing a subscription through a third party can break the terms of service."
  ],
  "note": "note-free-tokens-proxy.md"
}
```
