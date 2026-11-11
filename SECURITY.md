# Security

Top Annotator reads `/proc` and writes a small folder of YAML. It never
signals, terminates or writes to another process, and makes no network call.

The audit it writes is a trust list, so it is a target. By default anything
running as you can rewrite it. What that means and how to harden an install
is in [docs/hardening.md](docs/hardening.md).

To report a vulnerability, open a private security advisory on the repository
rather than a public issue, and say which version it concerns. The latest
release is the one supported.
