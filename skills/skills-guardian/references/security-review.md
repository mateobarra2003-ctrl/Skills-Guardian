# Security review guide

Use it in step 2 of the protocol. What matters is **what the install could do on the user's
computer and with their data**, not how popular it is.

## 1. Trust in the source (always)

Check with the GitHub API (`curl -s https://api.github.com/repos/<owner>/<repo>` and
`/users/<owner>`), or `gh api` if the GitHub CLI is available:

| Signal | Trustworthy | Suspicious |
|---|---|---|
| Author | Real name, company or **verified** organization, long history | Anonymous, new account, few repositories |
| Stars | Growth consistent with the repository's age | Thousands of stars in a few weeks: they can be bought |
| License | MIT, Apache-2.0 or similar | None, or restrictive |
| Activity | Recent commits, issues answered | Abandoned, or hundreds of unanswered issues |
| Security | `SECURITY.md`, no serious advisories | Critical CVEs (`/repos/<o>/<r>/security-advisories`) |

A well-known name does not exempt you from reading the files that **run** (section 2). It only
exempts you from auditing every line of plain instructions.

## 2. What to read in the files

Clone with `git clone --depth 1` into a **new, empty** temporary folder. Never run anything from
inside the clone, and use `python -I` when analyzing it with Python. On Windows, very deep paths
can make the checkout fail; if so, check that the files you need exist and match the commit
(`git ls-tree -r HEAD <path>` and `git hash-object <file>`).

Review **every** file in the folder that would be installed, not only `SKILL.md`:

- **Hooks** (`hooks.json`, `hooks/`, a `"hooks"` key in `plugin.json`): they run **on their own**,
  on every session, message or tool call. This is the biggest risk. Understand what each one does.
- **Automatic commands in `SKILL.md`**: lines like `` !`command` `` run when the skill loads.
  Check which interpreter they call and whether they install anything.
- **Scripts** (`.py`, `.js`, `.sh`, `.ps1`): look for network access (`fetch`, `requests`, `curl`,
  `http`), process execution (`child_process`, `subprocess`, `exec`, `eval`), credential reads
  (`.ssh`, `*_TOKEN`, `*_API_KEY`, keychains), writes outside the project, obfuscated code
  (`base64`, `atob`, `FromBase64`) and downloads that get executed (`curl … | sh`, `iex`).
- **`allowed-tools`** in the `SKILL.md` front matter: it grants tools **without asking**.
- **Instructions in the text** that tell Claude to install more things, use `-y` or `--yes`, edit
  `settings.json` or `CLAUDE.md`, send data to a URL, or turn off confirmations.
- **MCP servers** (`.mcp.json`, `mcpServers`): which server starts, whether it is downloaded with
  `npx` or `uvx` on every use, and what it can access.
- **Installers** (`install.sh`, `install.ps1`, `<tool> install`, `/plugin install`): read which
  files they touch before considering running them. Prefer copying only the needed folder by hand.

## 3. Risks that are not malice (they go in the note too)

- **Over-triggering:** descriptions like "use for any coding task" or "any question about X" can
  push aside the user's own skills.
- **Clashes** with installed skills: same name, same tasks or contradictory rules.
- **Huge packs** (hundreds of skills, dozens of hooks): install only what is useful.
- **Telemetry and advertising:** record whether usage data is sent and how to turn it off.
- **Privacy:** does it send documents, PDFs or code to external APIs? Projects may have private
  data folders (see `profile.projects` in the register).
- **Terms of service:** proxies or "gateways" that reuse a Claude subscription through a third
  party can break the terms and put the account at risk.
- **Automatic updates:** what was reviewed today can change tomorrow. Pin the reviewed version or
  commit and write it in the note.
- **Unpinned self-installs:** a skill that runs `pip install` or `npm install` without a version
  installs whatever is newest, into whichever interpreter it finds.

## 4. Verdict

| Verdict | When | What to do |
|---|---|---|
| ✅ Installable | Trustworthy source, nothing runs on its own, or what runs was read and is clean | Propose a location |
| ⚠️ Installable with adjustments | Useful, but with invasive hooks, self-installs, very broad triggers or data sent out | Propose installing **without** those parts, or with adjustments recorded in the header |
| ❌ Reject | Malicious, critical unpatched CVE, access to credentials or prompts, terms-of-service risk, or no real value | Record it as `rejected` with its reasons |
