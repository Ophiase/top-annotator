# Claude Code

@../AGENTS.md

The shared, tool-neutral rules are in the imported `AGENTS.md`. The skills
live in `.agents/skills/`; `.claude/skills/` only links to them. There is no
Claude-specific hook or permission layer; keep it that way until the workflow
actually needs one.

Read `.agents/rules/python.md` before Python work and `.agents/rules/tui.md`
before any Textual work.
