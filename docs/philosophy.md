# Do not trust me

A security tool asks for trust. This one asks you to withhold it.

## Why this project is agent-native

We are in the age of agents. Anyone with Claude, Cline, Codex or a local model
can now afford what used to cost a security team: intelligence made to measure
for their own machine.

- A generic tool guesses what is normal for everyone.
- Your agent can learn what is normal **for you**, and explain the rest.
- So the tool stays small and dumb; the intelligence lives in the agent you
  already trust, reading evidence the tool gathers.

That is why the CLI speaks JSON, why the audit is plain YAML, and why the
repository carries its own [agent rules](../AGENTS.md) and an
[`audit` skill](../.agents/skills/audit/SKILL.md).

## What I recommend

1. **Do not trust this code blindly.** It is one person's tool, published
   as is. Ask your agent to review it before you run it.
2. **Do not trust my audit.** The bundled base is what I decided for my
   machine. Your agent should check each entry against your packages.
3. **Copy it and let your agent maintain it.** Clone it into a repository of
   your own rather than a GitHub fork: a copy tuned to your machine and your
   threat model beats a shared one you do not read, and it owes nothing
   upstream.
4. **Keep your agent in the loop, not in charge.** It proposes; you confirm
   every write. See [hardening.md](hardening.md) for why.

## Learn from other copies

A copy does not have to live alone. Your agent can keep a short list of
copies it has reviewed and, now and then, look at what their authors added:

```yaml
# trust-repos.yaml, in your copy
repos:
  - url: https://github.com/<someone>/top-annotator
    reviewed: 2026-11-11
    take: [heuristics, base audit for arch]
    never: [code that writes outside the audit folder]
```

- Your agent reads their changes, explains them, and proposes what to port.
- You decide what lands in your copy, one change at a time.
- A listed repository is a source of ideas, never a source of truth: what it
  ships is reviewed like any other code.

This is a convention for your agent, not a feature of the tool: nothing here
fetches anything on its own.
