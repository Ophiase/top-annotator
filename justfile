mod agent 'agent.just'

[group("user")]
[doc("Install the command from this working tree, editable: a change here is live")]
@install:
    uv tool install --editable --force .

[group("user")]
@run:
    uv run top-annotator

[group("dev")]
@sync:
    uv sync --all-groups

[group("dev")]
@lint:
    uv run ruff check .
    uv run ruff format --check .
    uv run ty check .

[group("dev")]
@fmt:
    uv run ruff check . --fix
    uv run ruff format .

[group("dev")]
@test:
    uv run pytest

[group("dev")]
@check:
    just agent::checks

[group("dev")]
@guards:
    just agent::guards

[group("dev")]
@gate:
    just agent::gate

[group("dev")]
@checks:
    just agent::checks

[default]
@_list:
    just -l

[group("dev")]
[doc("Known vulnerabilities (CVE) in the locked dependencies; asks the network, so it stays out of the gate")]
@audit:
    uv audit --preview-features audit

[group("dev")]
[doc("Record the demo machine as docs/media/demo.gif; needs ImageMagick's convert")]
@gif:
    uv run --with cairosvg python -m tools.record_demo docs/media/demo.gif
