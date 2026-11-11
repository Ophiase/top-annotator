ALL = "all"
UNREVIEWED = "unreviewed"
NETWORK = "network"

FILTERS: dict[str, str] = {
    ALL: "every process",
    UNREVIEWED: "only what is left to audit",
    NETWORK: "only processes listening on a socket",
}
