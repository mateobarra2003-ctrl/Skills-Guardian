# Skills Guardian

[![tests](https://github.com/mateobarra2003-ctrl/Skills-Guardian/actions/workflows/tests.yml/badge.svg)](https://github.com/mateobarra2003-ctrl/Skills-Guardian/actions/workflows/tests.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**English** · [Español](README.es.md)

A [Claude Code](https://code.claude.com) skill that makes Claude **review skills, plugins and MCP
servers before installing them**, and keeps a local HTML register of what you installed, what you
left out and why.

![The register page: an index of installed skills grouped by location](docs/register-index.jpg)

## Why

A skill is a set of instructions that Claude follows as if you had written them. A plugin can also
run code on its own (hooks), and an MCP server can see your data. Skills spread through videos and
social media, and most people install them without reading them.

Skills Guardian makes Claude stop and check first. It does not block you: it tells you what the
thing really is, what it would do on your computer, how it would affect your projects, and only
installs it when you say yes.

## What it does

- **A 7-step protocol before every install.** Claude identifies what the link really points to,
  checks the author and the code (especially anything that runs on its own), writes an evaluation
  note, proposes where and how to install it, waits for your "yes", installs and verifies the copy,
  and updates your register.
- **Selective installs.** From a pack of hundreds of skills, only the ones you need. Hooks and
  self-installers are left out when the skills work without them. Heavy programs go into isolated
  environments with a pinned version.
- **Evaluation notes** in Markdown, one per review, with how each of your projects would be affected.
- **A register page** you open in your browser:
  - an index of every skill, grouped by location (global or per project);
  - a card per skill with what was installed, what each part does, what was left out, when it
    triggers, example requests, and a button to copy an "explain this skill to me in detail" request;
  - the rejected items, with their reasons;
  - a description of the protocol, for anyone you share the page with.
- **An audit** that flags skills installed without going through the protocol.
- **English and Spanish.** Claude answers in your language; the page labels follow the register's
  language.

![A card: what was installed, what each part does and what was left out](docs/register-card.jpg)

## Install

Requirements: Claude Code, Python 3.9 or newer (standard library only), and git (to review
repositories).

Fittingly, you should read [`SKILL.md`](skills/skills-guardian/SKILL.md) before installing this.
Skills Guardian has **no hooks, no MCP server and no automatic commands**. Its only script runs
when Claude calls it, and it touches only the register files.

**Option A: as a Claude Code plugin**

```
/plugin marketplace add mateobarra2003-ctrl/Skills-Guardian
/plugin install skills-guardian@skills-guardian
```

**Option B: copy the folder** (the skill is then available in every project)

macOS / Linux:

```bash
git clone --depth 1 https://github.com/mateobarra2003-ctrl/Skills-Guardian.git
cp -r Skills-Guardian/skills/skills-guardian ~/.claude/skills/
```

Windows (PowerShell):

```powershell
git clone --depth 1 https://github.com/mateobarra2003-ctrl/Skills-Guardian.git
Copy-Item -Recurse Skills-Guardian\skills\skills-guardian "$HOME\.claude\skills\"
```

**Option C: with the skills CLI**

```bash
npx skills add mateobarra2003-ctrl/Skills-Guardian
```

Then open a **new** Claude Code session: skills load at startup.

## First run

Ask Claude something like *"Set up Skills Guardian"*, or go straight to *"Is this skill safe?
https://github.com/…"*. The first time, Claude:

1. creates your register in `~/.claude/skills-guardian/` (or another folder you choose);
2. asks which language the page should use;
3. asks briefly about your projects, so each evaluation can say how it affects them;
4. lists the skills you already had, so you can evaluate them later.

Open `~/.claude/skills-guardian/registry.html` in your browser to see the register.

## Examples

- *"I saw this skill in a video. Is it safe? https://github.com/someone/cool-skills"*
- *"Install only the PDF skills from this repo, in my reports project."*
- *"Uninstall pdf-tables and update my register."*
- *"Audit my skills: is anything installed that didn't go through the guardian?"*
- *"Instala esta skill: https://github.com/…"* (works in Spanish too)

## Where things live

| What | Default location |
|---|---|
| The skill | `~/.claude/skills/skills-guardian/` (or the plugin folder) |
| Register (data) | `~/.claude/skills-guardian/registry.json` |
| Register page | `~/.claude/skills-guardian/registry.html` |
| Evaluation notes | `~/.claude/skills-guardian/notes/` |

To keep them somewhere else (for example a documents folder), Claude runs
`registry.py init --home <folder>`, and a small `~/.claude/skills-guardian/config.json` points to it.

The script can also be used directly:

| Command | What it does |
|---|---|
| `python3 scripts/registry.py where` | Shows the register, page and notes in use |
| `python3 scripts/registry.py init --language en` | Creates a new register |
| `python3 scripts/registry.py update` | Validates the register and rebuilds the page |
| `python3 scripts/registry.py audit` | Compares the skills on disk with the register |
| `python3 scripts/registry.py compare SRC DST` | Compares two folders file by file |

The register format is documented in
[`references/registry-format.md`](skills/skills-guardian/references/registry-format.md), and
[`examples/registry-example.json`](examples/registry-example.json) is a complete example.

## Privacy and limits

- **Everything stays on your computer.** The register, the notes and the page are local files.
  Nothing is uploaded unless you decide to publish the page yourself.
- **No telemetry.** Network access only happens during a review you asked for: the GitHub API, a
  `git clone` of the repository under review, or an optional `npx skills find` search with
  telemetry turned off.
- **It lowers the risk; it does not eliminate it.** A review is a careful reading assisted by an
  AI, not a guarantee. Claude says what it did not check, and you always have the last word.

## Uninstall

- Plugin: `/plugin uninstall skills-guardian@skills-guardian`
- Copied folder: delete `~/.claude/skills/skills-guardian/`
- Your data: delete `~/.claude/skills-guardian/` (only if you no longer want the register)

## Contributing

Issues and pull requests are welcome. Run the tests with:

```bash
python -m unittest discover -s tests -v
```

To add a language, add its texts to `TEXT` in
[`scripts/registry.py`](skills/skills-guardian/scripts/registry.py) and to `T` in
[`assets/registry-template.html`](skills/skills-guardian/assets/registry-template.html).
To report a security problem, see [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE). Skills Guardian started as a personal skill for reviewing skills found on social
media, and was generalized so anyone can use it.
