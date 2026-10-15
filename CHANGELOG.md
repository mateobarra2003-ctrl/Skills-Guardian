# Changelog

All notable changes to Skills Guardian are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow
[Semantic Versioning](https://semver.org/).

## [1.0.1] - 2026-10-15

### Fixed
- `SKILL.md` contained an example of the load-time command syntax (an exclamation mark followed
  by a command in backticks). Claude Code treats that syntax as a command to run when the skill
  loads, so the example itself was interpreted as one. The text now describes the syntax without
  using it, and a test keeps it out of `SKILL.md`.

## [1.0.0] - 2026-10-14

First public release.

### Added
- The 7-step installation protocol: identify, review trust and code, write a note, propose a
  location, wait for the user's "yes", install and verify, update the register.
- Security review guide, evaluation note template and register format reference.
- `registry.py` with `where`, `init`, `update`, `audit` and `compare` (a portable `diff -r`).
- A bilingual (English and Spanish) register page, rebuilt from a template on every update:
  index, locations, chains, cards with what was installed and left out, example requests, a
  "full explanation" request to copy, rejected items, and a description of the protocol.
- First-run setup that records the user's language and projects, and lists skills installed
  before the register.
- Installation as a Claude Code plugin, by copying the folder, or with `npx skills add`.
- Tests on Linux, macOS and Windows.

### Before 1.0
Skills Guardian started as a personal Spanish skill called `guardian-de-skills`, with paths and
projects specific to its author. Version 1.0.0 generalizes it for anyone.
