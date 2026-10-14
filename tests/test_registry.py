"""Tests for skills/skills-guardian/scripts/registry.py (standard library only).

Run from the repository root:  python -m unittest discover -s tests -v
"""
import contextlib
import importlib.util
import io
import json
import os
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "skills-guardian"

spec = importlib.util.spec_from_file_location("registry", SKILL / "scripts" / "registry.py")
registry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(registry)


def run(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = registry.main(list(argv))
    return code, out.getvalue()


class Sandbox(unittest.TestCase):
    """Each test gets a fake home: ~/.claude/skills and ~/.claude/skills-guardian live in a temp dir."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.skills = self.home / ".claude" / "skills"
        self.skills.mkdir(parents=True)
        self._saved = (registry.DEFAULT_HOME, registry.CLAUDE_SKILLS, os.environ.pop("SKILLS_GUARDIAN_REGISTRY", None))
        registry.DEFAULT_HOME = self.home / ".claude" / "skills-guardian"
        registry.CLAUDE_SKILLS = self.skills

    def tearDown(self):
        registry.DEFAULT_HOME, registry.CLAUDE_SKILLS, env = self._saved
        if env is not None:
            os.environ["SKILLS_GUARDIAN_REGISTRY"] = env
        self.tmp.cleanup()

    def make_skill(self, folder: Path, name: str, body: str = "x") -> Path:
        d = folder / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: test\n---\n{body}\n", encoding="utf-8")
        return d

    def init(self, *extra):
        code, out = run("init", *extra)
        self.assertEqual(code, 0, out)
        return registry.DEFAULT_HOME / "registry.json"

    def load(self, path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def save(self, path, data):
        Path(path).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


class TestInit(Sandbox):
    def test_creates_register_page_and_notes(self):
        self.make_skill(self.skills, "old-skill")
        reg = self.init("--language", "es")
        r = self.load(reg)
        self.assertEqual(r["language"], "es")
        self.assertEqual(r["preexisting"], ["old-skill"])
        self.assertEqual(r["entries"][0]["name"], "skills-guardian")
        self.assertTrue(Path(r["html"]).exists())
        self.assertTrue(Path(r["notes_dir"]).is_dir())
        self.assertIn("<title>Registro de skills</title>", Path(r["html"]).read_text(encoding="utf-8"))

    def test_refuses_to_overwrite_without_force(self):
        self.init()
        code, out = run("init")
        self.assertEqual(code, 1)
        self.assertIn("already exists", out)
        self.assertEqual(run("init", "--force")[0], 0)

    def test_custom_home_writes_pointer(self):
        custom = self.home / "Documents" / "skills"
        code, out = run("init", "--home", str(custom))
        self.assertEqual(code, 0, out)
        config = self.load(registry.DEFAULT_HOME / "config.json")
        self.assertEqual(Path(config["registry"]), custom / "registry.json")
        self.assertEqual(registry.registry_path(None), custom / "registry.json")


class TestLookup(Sandbox):
    def test_order_arg_env_config_default(self):
        default = registry.DEFAULT_HOME / "registry.json"
        self.assertEqual(registry.registry_path(None), default)
        registry.DEFAULT_HOME.mkdir(parents=True)
        (registry.DEFAULT_HOME / "config.json").write_text(json.dumps({"registry": "/from/config.json"}), encoding="utf-8")
        self.assertEqual(registry.registry_path(None), Path("/from/config.json"))
        os.environ["SKILLS_GUARDIAN_REGISTRY"] = "/from/env.json"
        try:
            self.assertEqual(registry.registry_path(None), Path("/from/env.json"))
            self.assertEqual(registry.registry_path("/from/arg.json"), Path("/from/arg.json"))
        finally:
            del os.environ["SKILLS_GUARDIAN_REGISTRY"]


class TestUpdateAndValidation(Sandbox):
    def good_entry(self, **over):
        e = {
            "name": "demo", "kind": "skill", "location": "global", "status": "installed", "date": "2026-10-14",
            "source": "me · demo", "summary": "Demo", "what": "Demo skill.", "triggers": "Never.",
            "examples": ["Use the demo </script> here."], "note": "note-demo.md",
            "installed": [{"part": "SKILL.md", "purpose": "Instructions.",
                           "elements": [{"name": "A", "purpose": "a"}, {"name": "B", "purpose": "b"}]}],
            "left_out": ["Nothing: all of it."],
        }
        e.update(over)
        return e

    def test_update_renders_and_escapes(self):
        reg = self.init()
        r = self.load(reg)
        r["entries"].append(self.good_entry())
        self.save(reg, r)
        code, out = run("update")
        self.assertEqual(code, 0, out)
        page = Path(r["html"]).read_text(encoding="utf-8")
        self.assertIn("<\\/script> here", page)
        block = re.search(r'<script id="registry" type="application/json">(.*?)</script>', page, re.S).group(1)
        data = json.loads(block)
        self.assertEqual(data["registry_file"], str(reg.resolve()))

    def test_incomplete_entry_is_rejected_and_page_untouched(self):
        reg = self.init()
        r = self.load(reg)
        before = Path(r["html"]).read_text(encoding="utf-8")
        bad = self.good_entry(name="bad", location="mars", kind="extension")
        del bad["left_out"]
        thin = self.good_entry(name="thin")
        thin["installed"][0]["elements"] = [{"name": "only one", "purpose": "x"}]
        r["entries"] += [bad, thin]
        self.save(reg, r)
        code, out = run("update")
        self.assertEqual(code, 1)
        for fragment in ("location 'mars'", "kind 'extension'", "left_out", "'elements'"):
            self.assertIn(fragment, out)
        self.assertEqual(Path(r["html"]).read_text(encoding="utf-8"), before)

    def test_summary_length_and_chain_warning(self):
        reg = self.init()
        r = self.load(reg)
        r["entries"].append(self.good_entry(summary="x" * 60))
        self.save(reg, r)
        self.assertIn("45 characters", run("update")[1])
        r["entries"][-1]["summary"] = "ok"
        r["chains"] = [{"title": "Flow", "steps": [{"skill": "missing-skill"}, {"label": "Your yes"}]}]
        self.save(reg, r)
        code, out = run("update")
        self.assertEqual(code, 0, out)
        self.assertIn("not an installed entry", out)

    def test_rejected_entry_needs_no_install_fields(self):
        reg = self.init()
        r = self.load(reg)
        r["entries"].append({"name": "nope", "kind": "program", "location": None, "status": "rejected",
                             "date": "2026-10-14", "source": "x", "what": "x", "note": "note-nope.md",
                             "reasons": ["Unsafe."]})
        self.save(reg, r)
        self.assertEqual(run("update")[0], 0)


class TestAudit(Sandbox):
    def test_detects_unregistered_and_missing(self):
        reg = self.init()
        r = self.load(reg)
        r["entries"].append(TestUpdateAndValidation.good_entry(self, name="gone"))
        self.save(reg, r)
        self.make_skill(self.skills, "sneaky")
        code, out = run("audit")
        self.assertEqual(code, 2)
        self.assertIn("sneaky", out)
        self.assertIn("gone", out)

    def test_clean_audit(self):
        self.init()
        code, out = run("audit")
        self.assertEqual(code, 0, out)


class TestCompare(Sandbox):
    def test_identical_changed_and_expected(self):
        a = self.make_skill(self.home / "a", "s", "same")
        b = self.make_skill(self.home / "b", "s", "same")
        (a / "scripts").mkdir()
        (a / "scripts" / "test.py").write_text("x", encoding="utf-8")
        self.assertEqual(run("compare", str(a), str(b))[0], 1)
        self.assertEqual(run("compare", str(a), str(b), "--expect-missing", "scripts")[0], 0)
        (b / "SKILL.md").write_text("changed", encoding="utf-8")
        self.assertEqual(run("compare", str(a), str(b), "--expect-missing", "scripts")[0], 1)
        code, out = run("compare", str(a), str(b), "--expect-missing", "scripts", "--expect-changed", "SKILL.md")
        self.assertEqual(code, 0, out)


class TestPackage(unittest.TestCase):
    def test_skill_front_matter(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        front = text.split("---", 2)[1]
        name = re.search(r"^name:\s*(\S+)", front, re.M).group(1)
        desc = re.search(r"^description:\s*(.+)$", front, re.M).group(1)
        self.assertEqual(name, SKILL.name)
        self.assertRegex(name, r"^[a-z0-9]+(-[a-z0-9]+)*$")
        self.assertLessEqual(len(desc), 1024)

    def test_template_has_markers_and_both_languages(self):
        page = (SKILL / "assets" / "registry-template.html").read_text(encoding="utf-8")
        self.assertRegex(page, r"(?s)<!-- REGISTRY:START -->.*<!-- REGISTRY:END -->")
        for key in ("en: {", "es: {"):
            self.assertIn(key, page)

    def test_plugin_manifests_agree(self):
        plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(plugin["version"], registry.VERSION)
        self.assertEqual(market["plugins"][0]["name"], plugin["name"])
        self.assertEqual(market["plugins"][0]["version"], plugin["version"])


if __name__ == "__main__":
    unittest.main()
