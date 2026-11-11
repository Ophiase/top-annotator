set positional-arguments := true

import ".agents/portable/just/harness.just"

# Markdown + lint + format check + type check + tests, one command.
[group("agent")]
@checks:
    rumdl check .
    uv run ruff check .
    uv run ruff format --check .
    uv run ty check .
    uv run pytest -q

[group("agent")]
[doc("Run the portable and project checks over every changed file")]
[script("bash")]
guards:
    status=0
    for check in markdown markdown-smell french comment-slop no-suppression no-module-docstring one-class no-protocol callable-alias hardcoded-url portable folder-size yaml-extension config-format file-length version; do
        .agents/portable/checks/changed-files.sh | xargs -r -d '\n' .agents/checks/run.sh "$check" || status=1
    done
    exit $status

[group("agent")]
[doc("VERSION, pyproject, the package, CITATION.cff and CHANGELOG.md must agree")]
@version:
    .agents/checks/version.sh && cat VERSION
