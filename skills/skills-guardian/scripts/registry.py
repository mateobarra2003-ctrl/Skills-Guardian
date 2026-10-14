#!/usr/bin/env python3
"""Skills Guardian register tool (standard library only, Python 3.9+).

Keeps a JSON register of everything that was installed, adjusted or rejected through the
Skills Guardian protocol, and renders it into one self-contained HTML page.

Commands
  where             Show which register, page and notes folder are in use.
  init              Create a new register (and its page) for this user.
  update            Validate the register and rebuild the HTML page from the template.
  audit             Compare the skill folders on disk with the register.
  compare SRC DST   Compare two folders file by file (a portable `diff -r`).

Register lookup order: --registry, $SKILLS_GUARDIAN_REGISTRY,
~/.claude/skills-guardian/config.json ("registry" key), ~/.claude/skills-guardian/registry.json.
"""
from __future__ import annotations

import argparse
import filecmp
import html
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

VERSION = "1.0.0"
REPO_URL = "https://github.com/mateobarra2003-ctrl/Skills-Guardian"

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "assets" / "registry-template.html"
DEFAULT_HOME = Path.home() / ".claude" / "skills-guardian"
CLAUDE_SKILLS = Path.home() / ".claude" / "skills"

MARKERS = re.compile(r"(<!-- REGISTRY:START -->)(.*?)(<!-- REGISTRY:END -->)", re.S)
TITLE_TAG = re.compile(r"<title>.*?</title>", re.S)
SCHEMA = 1
KINDS = {"skill", "plugin", "mcp", "hook", "program"}
STATUSES = {"installed", "rejected"}
LANGUAGES = {"en", "es"}
REQUIRED = {"name", "kind", "status", "date", "source", "what", "note"}
REQUIRED_INSTALLED = {"location", "triggers", "examples", "summary", "installed", "left_out"}
SUMMARY_MAX = 45
IGNORED_PARTS = {".git", "__pycache__", ".DS_Store"}

TEXT = {
    "en": {
        "title": "Skills Register",
        "global_desc": "Available in every session, in any folder.",
        "plugin_desc": "Installed as a Claude Code plugin.",
        "notes_prefix": "note-",
        "self": {
            "summary": "Install safely and keep this register",
            "what": "Runs a prudence protocol before anything that extends Claude is installed, and keeps this register up to date.",
            "triggers": "Before evaluating, installing, adjusting or removing skills, plugins, MCP servers, hooks or programs for Claude, even when it is not named.",
            "examples": [
                "Evaluate this skill before I install it: https://github.com/owner/repo",
                "Install the skill X in this project.",
                "Remove the skill Y and update my skills register.",
            ],
            "not_triggered_by": "Install pandas in this project (a normal project dependency).",
            "note": "The skill's own SKILL.md",
            "installed": [
                {"part": "SKILL.md", "purpose": "The protocol Claude follows before installing anything, and how to keep this register.",
                 "elements": [
                     {"name": "First run", "purpose": "Creates the register and asks about your projects so evaluations can say how each one is affected."},
                     {"name": "Installation protocol (7 steps)", "purpose": "Identify what it really is, review trust and code, write a note, propose a location, wait for your yes, install and verify, update the register."},
                     {"name": "Uninstall, adjust or reject", "purpose": "How each case is recorded, including the reasons for a rejection."},
                     {"name": "Keeping the register", "purpose": "Which fields each card needs, how to run registry.py and how to audit drift."},
                     {"name": "What to report", "purpose": "The order of the answer: what it is, verdict, location, note and a concrete question."},
                 ]},
                {"part": "references/security-review.md", "purpose": "What to check in hooks, scripts and permissions, and when to reject."},
                {"part": "references/note-template.md", "purpose": "The format of the evaluation notes."},
                {"part": "references/registry-format.md", "purpose": "Every field of the register, with an example card."},
                {"part": "scripts/registry.py", "purpose": "Creates and validates the register, rebuilds this page, audits drift and compares folders."},
                {"part": "assets/registry-template.html", "purpose": "The design of this page; the data is inserted on every update."},
            ],
            "left_out": ["Nothing: this is the whole skill."],
        },
    },
    "es": {
        "title": "Registro de skills",
        "global_desc": "Disponibles en todas las sesiones, en cualquier carpeta.",
        "plugin_desc": "Instalada como plugin de Claude Code.",
        "notes_prefix": "nota-",
        "self": {
            "summary": "Instalar con prudencia y llevar este registro",
            "what": "Aplica un protocolo de prudencia antes de instalar cualquier cosa que amplíe a Claude, y mantiene este registro al día.",
            "triggers": "Antes de evaluar, instalar, ajustar o desinstalar skills, plugins, servidores MCP, hooks o programas para Claude, aunque no se la nombre.",
            "examples": [
                "Evalúa esta skill antes de instalarla: https://github.com/autor/repo",
                "Instala la skill X en este proyecto.",
                "Desinstala la skill Y y actualiza mi registro de skills.",
            ],
            "not_triggered_by": "Instala pandas en este proyecto (una dependencia normal del proyecto).",
            "note": "El SKILL.md de la propia skill",
            "installed": [
                {"part": "SKILL.md", "purpose": "El protocolo que sigue Claude antes de instalar algo, y cómo mantener este registro.",
                 "elements": [
                     {"name": "Primer uso", "purpose": "Crea el registro y pregunta por tus proyectos para que cada evaluación diga cómo los afecta."},
                     {"name": "Protocolo de instalación (7 pasos)", "purpose": "Identificar qué es, revisar confiabilidad y código, escribir la nota, proponer ubicación, esperar tu sí, instalar y verificar, actualizar el registro."},
                     {"name": "Desinstalar, ajustar o descartar", "purpose": "Cómo se registra cada caso, incluidas las razones de un descarte."},
                     {"name": "Mantener el registro", "purpose": "Qué campos lleva cada ficha, cómo ejecutar registry.py y cómo detectar diferencias."},
                     {"name": "Qué informar", "purpose": "El orden de la respuesta: qué es, veredicto, ubicación, nota y una pregunta concreta."},
                 ]},
                {"part": "references/security-review.md", "purpose": "Qué revisar en hooks, scripts y permisos, y cuándo descartar."},
                {"part": "references/note-template.md", "purpose": "El formato de las notas de evaluación."},
                {"part": "references/registry-format.md", "purpose": "Todos los campos del registro, con una ficha de ejemplo."},
                {"part": "scripts/registry.py", "purpose": "Crea y valida el registro, reconstruye esta página, detecta diferencias y compara carpetas."},
                {"part": "assets/registry-template.html", "purpose": "El diseño de esta página; los datos se insertan en cada actualización."},
            ],
            "left_out": ["Nada: es la skill completa."],
        },
    },
}


# ---------------------------------------------------------------- paths and I/O

def registry_path(arg: str | None) -> Path:
    if arg:
        return Path(arg).expanduser()
    env = os.environ.get("SKILLS_GUARDIAN_REGISTRY")
    if env:
        return Path(env).expanduser()
    config = DEFAULT_HOME / "config.json"
    if config.exists():
        try:
            pointed = json.loads(config.read_text(encoding="utf-8")).get("registry")
            if pointed:
                return Path(pointed).expanduser()
        except (OSError, ValueError):
            pass
    return DEFAULT_HOME / "registry.json"


def resolve(value: str, reg_path: Path) -> Path:
    """Paths inside the register may be absolute or relative to the register file."""
    p = Path(value).expanduser()
    return p if p.is_absolute() else (reg_path.resolve().parent / p)


def load(reg_path: Path) -> dict:
    with reg_path.open(encoding="utf-8") as f:
        return json.load(f)


def write_text(path: Path, text: str) -> None:
    """UTF-8 with LF line endings on every OS (Path.write_text has no `newline` before 3.10)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def save(reg_path: Path, r: dict) -> None:
    write_text(reg_path, json.dumps(r, ensure_ascii=False, indent=2) + "\n")


def with_sep(p: Path) -> str:
    return str(p) + os.sep


# ---------------------------------------------------------------- validation

def validate(r: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if r.get("schema") != SCHEMA:
        errors.append(f"'schema' must be {SCHEMA} (found {r.get('schema')!r})")
    if r.get("language") not in LANGUAGES:
        errors.append(f"'language' must be one of {sorted(LANGUAGES)}")
    for key in ("html", "notes_dir"):
        if not r.get(key):
            errors.append(f"missing '{key}'")

    locations = r.get("locations", {})
    if not isinstance(locations, dict) or not locations:
        errors.append("'locations' must have at least one location")
        locations = {}
    for key, loc in locations.items():
        if not isinstance(loc, dict) or not loc.get("label") or not loc.get("path"):
            errors.append(f"location '{key}': needs 'label' and 'path'")

    seen = set()
    installed_names = set()
    for i, e in enumerate(r.get("entries", [])):
        name = e.get("name", f"#{i}")
        missing = REQUIRED - e.keys()
        status = e.get("status")
        if status == "installed":
            missing |= REQUIRED_INSTALLED - e.keys()
            installed_names.add(name)
            if e.get("location") not in locations:
                errors.append(f"{name}: location '{e.get('location')}' is not in 'locations'")
        if missing:
            errors.append(f"{name}: missing fields {sorted(missing)}")
        if e.get("kind") not in KINDS:
            errors.append(f"{name}: kind '{e.get('kind')}' is not one of {sorted(KINDS)}")
        if status not in STATUSES:
            errors.append(f"{name}: status '{status}' is not one of {sorted(STATUSES)}")
        if status == "rejected" and not e.get("reasons"):
            warnings.append(f"{name}: rejected without 'reasons'")
        if status == "installed":
            parts = e.get("installed", [])
            if not isinstance(parts, list) or not parts or not all(
                    isinstance(p, dict) and p.get("part") and p.get("purpose") for p in parts):
                errors.append(f"{name}: 'installed' must be a list of {{part, purpose}}")
                parts = []
            if e.get("kind") == "skill":
                md = next((p for p in parts if str(p.get("part", "")).startswith("SKILL.md")), None)
                elems = (md or {}).get("elements", [])
                if not md:
                    errors.append(f"{name}: 'installed' must include the SKILL.md part")
                elif not isinstance(elems, list) or len(elems) < 2 or not all(
                        isinstance(x, dict) and x.get("name") and x.get("purpose") for x in elems):
                    errors.append(f"{name}: the SKILL.md part needs 'elements' (2 or more {{name, purpose}})")
            left = e.get("left_out", [])
            if not isinstance(left, list) or not left or not all(isinstance(x, str) and x for x in left):
                errors.append(f"{name}: 'left_out' must be a list of texts (use [\"Nothing: ...\"] if nothing was left out)")
            if not isinstance(e.get("examples", []), list) or not e.get("examples"):
                errors.append(f"{name}: 'examples' must be a non-empty list")
        if len(e.get("summary", "")) > SUMMARY_MAX:
            errors.append(f"{name}: 'summary' is for the index; {SUMMARY_MAX} characters at most")
        key = (name, e.get("location"))
        if key in seen:
            errors.append(f"{name}: duplicated in the same location")
        seen.add(key)

    for c in r.get("chains", []):
        if not isinstance(c, dict) or not c.get("title") or not isinstance(c.get("steps"), list):
            errors.append("each chain needs 'title' and a list of 'steps'")
            continue
        for s in c["steps"]:
            if not isinstance(s, dict) or not (s.get("skill") or s.get("label")):
                errors.append(f"chain '{c['title']}': each step needs 'skill' or 'label'")
            elif s.get("skill") and s["skill"] not in installed_names:
                warnings.append(f"chain '{c['title']}': '{s['skill']}' is not an installed entry")
    return errors, warnings


# ---------------------------------------------------------------- rendering

def render(r: dict, reg_path: Path) -> Path:
    if not TEMPLATE.exists():
        raise FileNotFoundError(f"template not found: {TEMPLATE}")
    page = TEMPLATE.read_text(encoding="utf-8")
    if not MARKERS.search(page):
        raise ValueError("the template has no REGISTRY:START/END markers")
    shown = dict(r, registry_file=str(reg_path.resolve()),
                 notes_dir=str(resolve(r["notes_dir"], reg_path)))
    data = json.dumps(shown, ensure_ascii=False).replace("</", "<\\/")
    block = f'\n<script id="registry" type="application/json">{data}</script>\n'
    page = MARKERS.sub(lambda m: m.group(1) + block + m.group(3), page, count=1)
    title = r.get("title") or TEXT[r.get("language", "en")]["title"]
    page = TITLE_TAG.sub(lambda m: f"<title>{html.escape(title)}</title>", page, count=1)
    out = resolve(r["html"], reg_path)
    write_text(out, page)
    return out


# ---------------------------------------------------------------- commands

def self_entry(language: str) -> tuple[str, dict, dict | None]:
    """The register always starts with Skills Guardian itself."""
    t = TEXT[language]
    if SKILL_DIR.parent.resolve() == CLAUDE_SKILLS.resolve():
        loc_key, loc = "global", None
    else:
        loc_key = "plugin"
        loc = {"label": "Plugin", "path": with_sep(SKILL_DIR.parent), "desc": t["plugin_desc"]}
    entry = {
        "name": SKILL_DIR.name, "kind": "skill", "location": loc_key, "status": "installed",
        "date": date.today().isoformat(),
        "source": f"Skills Guardian · {REPO_URL.replace('https://', '')} v{VERSION}",
        **t["self"],
    }
    return loc_key, entry, loc


def cmd_init(args) -> int:
    language = args.language
    home = Path(args.home).expanduser() if args.home else DEFAULT_HOME
    reg_path = home / "registry.json"
    if reg_path.exists() and not args.force:
        print(f"A register already exists at {reg_path}. Use 'update', or 'init --force' to start over.")
        return 1
    t = TEXT[language]
    preexisting = []
    if CLAUDE_SKILLS.exists():
        preexisting = sorted(p.parent.name for p in CLAUDE_SKILLS.glob("*/SKILL.md")
                             if p.parent.name != SKILL_DIR.name)
    loc_key, entry, plugin_loc = self_entry(language)
    locations = {"global": {"label": "Global", "path": with_sep(CLAUDE_SKILLS), "desc": t["global_desc"]}}
    if plugin_loc:
        locations[loc_key] = plugin_loc
    r = {
        "schema": SCHEMA,
        "language": language,
        "title": t["title"],
        "updated": date.today().isoformat(),
        "html": str(home / "registry.html"),
        "notes_dir": str(home / "notes"),
        "skill_dir": str(SKILL_DIR),
        "published_url": "",
        "profile": {"about": "", "projects": []},
        "locations": locations,
        "preexisting": preexisting,
        "chains": [],
        "entries": [entry],
    }
    errors, _ = validate(r)
    if errors:  # would mean a bug in this script
        print("Internal error, the new register is invalid:", *errors, sep="\n  - ")
        return 1
    save(reg_path, r)
    resolve(r["notes_dir"], reg_path).mkdir(parents=True, exist_ok=True)
    page = render(r, reg_path)
    if home != DEFAULT_HOME:
        config = DEFAULT_HOME / "config.json"
        if config.exists() and not args.force:
            print(f"Note: {config} already points somewhere; left untouched. "
                  f"Set it to {{\"registry\": \"{reg_path}\"}} to use this register by default.")
        else:
            DEFAULT_HOME.mkdir(parents=True, exist_ok=True)
            config.write_text(json.dumps({"registry": str(reg_path)}, indent=2) + "\n", encoding="utf-8")
    print(f"Register created: {reg_path}")
    print(f"Page:             {page}")
    print(f"Notes folder:     {resolve(r['notes_dir'], reg_path)}")
    if preexisting:
        print(f"Skills found that were installed before the register ({len(preexisting)}): {', '.join(preexisting)}")
    return 0


def cmd_where(args) -> int:
    reg_path = registry_path(args.registry)
    print(f"Skill folder: {SKILL_DIR}")
    print(f"Template:     {TEMPLATE}")
    print(f"Register:     {reg_path} ({'exists' if reg_path.exists() else 'NOT FOUND: run init'})")
    if not reg_path.exists():
        return 1
    r = load(reg_path)
    print(f"Language:     {r.get('language')}")
    print(f"Page:         {resolve(r.get('html', ''), reg_path)}")
    print(f"Notes folder: {resolve(r.get('notes_dir', ''), reg_path)}")
    print(f"Published at: {r.get('published_url') or '(not published)'}")
    for key, loc in r.get("locations", {}).items():
        print(f"Location {key!r}: {loc.get('label')} -> {loc.get('path')}")
    projects = r.get("profile", {}).get("projects", [])
    if projects:
        print("Projects:     " + "; ".join(f"{p.get('name')} ({p.get('path', '')})" for p in projects))
    return 0


def cmd_update(args) -> int:
    reg_path = registry_path(args.registry)
    if not reg_path.exists():
        print(f"No register at {reg_path}. Run 'init' first.")
        return 1
    r = load(reg_path)
    errors, warnings = validate(r)
    if errors:
        print("The register has errors; the page was not touched:")
        for e in errors:
            print("  -", e)
        return 1
    r["updated"] = date.today().isoformat()
    r["skill_dir"] = str(SKILL_DIR)
    save(reg_path, r)
    page = render(r, reg_path)
    entries = r.get("entries", [])
    installed = [e for e in entries if e["status"] == "installed"]
    rejected = sum(1 for e in entries if e["status"] == "rejected")
    print(f"Page updated ({r['updated']}): {page}")
    print(f"  {len(installed)} installed, {rejected} rejected")
    for key, loc in r["locations"].items():
        print(f"  {loc['label']}: {sum(1 for e in installed if e['location'] == key)}")
    for w in warnings:
        print("  warning:", w)
    if r.get("published_url"):
        print(f"Republish the page at: {r['published_url']}")
    return 0


def cmd_audit(args) -> int:
    reg_path = registry_path(args.registry)
    if not reg_path.exists():
        print(f"No register at {reg_path}. Run 'init' first.")
        return 1
    r = load(reg_path)
    preexisting = set(r.get("preexisting", []))
    differences = False
    for key, loc in r.get("locations", {}).items():
        folder = Path(loc["path"]).expanduser()
        on_disk = {p.parent.name for p in folder.glob("*/SKILL.md")} if folder.exists() else set()
        registered = {e["name"] for e in r.get("entries", [])
                      if e.get("status") == "installed" and e.get("location") == key and e.get("kind") == "skill"}
        unregistered = sorted(on_disk - registered - preexisting)
        missing = sorted(registered - on_disk)
        print(f"{loc['label']} ({folder}):")
        print(f"  on disk: {len(on_disk)} · registered: {len(registered)}")
        if unregistered:
            differences = True
            print("  Installed but NOT registered (did not go through the protocol):", ", ".join(unregistered))
        if missing:
            differences = True
            print("  Registered but NOT found (uninstalled?):", ", ".join(missing))
    if not differences:
        print("No differences: the register matches what is installed.")
    return 2 if differences else 0


def _files(root: Path) -> set[str]:
    return {p.relative_to(root).as_posix() for p in root.rglob("*")
            if p.is_file() and not (IGNORED_PARTS & set(p.relative_to(root).parts))}


def cmd_compare(args) -> int:
    src, dst = Path(args.src).expanduser(), Path(args.dst).expanduser()
    for p in (src, dst):
        if not p.is_dir():
            print(f"Not a folder: {p}")
            return 1
    a, b = _files(src), _files(dst)
    changed = sorted(f for f in a & b if not filecmp.cmp(src / f, dst / f, shallow=False))
    only_src, only_dst = sorted(a - b), sorted(b - a)
    expected_changed = set(args.expect_changed or [])
    expected_missing = tuple(m.rstrip("/") for m in (args.expect_missing or []))

    def is_expected_missing(f: str) -> bool:
        return any(f == m or f.startswith(m + "/") for m in expected_missing)

    unexpected = 0
    print(f"Compared {len(a)} file(s) in {src} with {len(b)} in {dst}.")
    for f in changed:
        ok = f in expected_changed
        unexpected += not ok
        print(f"  {'changed (expected)' if ok else 'CHANGED'}: {f}")
    for f in only_src:
        ok = is_expected_missing(f)
        unexpected += not ok
        print(f"  {'left out (expected)' if ok else 'MISSING in destination'}: {f}")
    for f in only_dst:
        unexpected += 1
        print(f"  EXTRA in destination: {f}")
    for f in sorted(expected_changed - set(changed)):
        print(f"  note: '{f}' was expected to change but is identical")
    print("Identical except for the expected differences." if unexpected == 0
          else f"{unexpected} unexpected difference(s).")
    return 0 if unexpected == 0 else 1


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="registry.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version=f"Skills Guardian {VERSION}")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("where", help="show the paths in use")
    s.add_argument("--registry")
    s.set_defaults(func=cmd_where)

    s = sub.add_parser("init", help="create a new register")
    s.add_argument("--language", choices=sorted(LANGUAGES), default="en")
    s.add_argument("--home", help=f"folder for the register, page and notes (default {DEFAULT_HOME})")
    s.add_argument("--force", action="store_true", help="overwrite an existing register")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("update", help="validate the register and rebuild the page")
    s.add_argument("--registry")
    s.set_defaults(func=cmd_update)

    s = sub.add_parser("audit", help="compare the skills on disk with the register")
    s.add_argument("--registry")
    s.set_defaults(func=cmd_audit)

    s = sub.add_parser("compare", help="compare two folders file by file")
    s.add_argument("src")
    s.add_argument("dst")
    s.add_argument("--expect-changed", nargs="*", metavar="FILE",
                   help="files you adjusted on purpose (relative paths, e.g. SKILL.md)")
    s.add_argument("--expect-missing", nargs="*", metavar="PATH",
                   help="files or folders you left out on purpose (e.g. scripts/tests)")
    s.set_defaults(func=cmd_compare)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
