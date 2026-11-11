# Working with an agent

The audit is shared state between a human and an agent. The human freezes a
view; the agent explains a process and proposes a level; the human decides.

## The JSON commands

```bash
top-annotator snapshot          # processes, trust, source, section
top-annotator rules             # effective session + audit rules
top-annotator annotate SIGNATURE trust --note "why"
top-annotator annotate SIGNATURE safe --provider distro
top-annotator annotate SIGNATURE safe --children a,b --exclusive --gui
top-annotator annotate SIGNATURE trust --terminal   # or --interactive
top-annotator annotate SIGNATURE safe --agents claude
top-annotator verify /usr/bin/x # package owner + dpkg -V
top-annotator undo
```

| Command | Tells the agent |
| --- | --- |
| `snapshot` | which signature is interesting, and what the base `suggested` for it |
| `rules` | what the human already decided, and from which layer |
| `annotate` | writes your layer, never the base |
| `verify` | the package and integrity evidence for one path |

## The `audit` skill

[.agents/skills/audit/](../.agents/skills/audit/SKILL.md), linked from
`.claude/skills/`, drives the CLI:

- `/audit analyse`: a read-only look that ends in a post-it report: a
  verdict, the counts, at most three processes worth a look, the next step;
- `/audit update`: proposes a level, a provider and a note per unannotated
  signature, then writes them where you choose, after you agree.

## What an agent must not be trusted with

- Process names and command lines are written by the processes themselves.
- A malicious one can carry text aimed at the agent reading it.
- So an agent's answer is a proposal: the human confirms every write. See
  [hardening.md](hardening.md).
