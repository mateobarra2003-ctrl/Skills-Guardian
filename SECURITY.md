# Security policy

Skills Guardian exists to make installing skills safer, so security reports are especially welcome.

## What is in scope

- `scripts/registry.py`: for example, writing outside the register's folders, or unsafe handling
  of paths or JSON.
- `assets/registry-template.html`: for example, text from a register entry that could run as code
  in the page.
- The instructions in `SKILL.md` and `references/`: for example, a gap that would let a malicious
  skill get installed without the user's approval, or that would make Claude run code from a
  repository under review.

A skill that Skills Guardian evaluated and judged wrongly is not a vulnerability in Skills
Guardian, but please open an issue: it helps improve the review guide.

## How to report

Please **do not open a public issue** for a vulnerability. Use GitHub's private reporting instead:
go to the **Security** tab of this repository and click **Report a vulnerability**.

You can expect a first answer within a week. Fixes are released as a new version and noted in the
[changelog](CHANGELOG.md).

## Supported versions

Only the latest release receives fixes.
