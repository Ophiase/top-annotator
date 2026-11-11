# The screen and the keys

## Keys

| Key | Effect |
| --- | --- |
| `j` / `k` | move down / up (arrows work too) |
| `g` / `G` | first / last row |
| `space`, `h`, `l` | toggle / fold / unfold the band, group or subtree under the cursor |
| `/` | fuzzy search; matching processes keep their **whole parent chain** |
| `Enter` | details: signature, executable, parents, note; on a header, the band or group |
| `s` | mark the selected process **TRUST** (lowest trust level) |
| `S` | choose the trust level precisely, or `unreviewed` to remove it |
| `A` | accept the base's suggestion for this process into your layer |
| `a` | cycle `trust → host → audited → safe → core → personal → watch → unsafe → unannotated` |
| `x` | remove the annotation |
| `u` | undo the latest change to your annotations, one step per press |
| `y` | copy the selected process with `wl-copy`, or OSC 52 without it |
| `n` | edit the note attached to the annotation |
| `f` | filter: `all`, `unreviewed`, `network` (listening processes) |
| `t` | cycle view: `sections → tree → flat` |
| `R` | review the effective rules, last changed first, with fuzzy search |
| `p` | freeze / resume the automatic scan |
| `r` | rescan once, even while frozen |
| `Esc` | clear the search |
| `q` | quit |

The footer shows the bindings that matter day to day; `Ctrl+P` lists the
rest.

## Three bands

The default view groups processes by urgency:

| Band | Holds |
| --- | --- |
| `WEIRD` | a masquerade, an executable in `/tmp` or `/dev/shm`, a deleted executable, a zombie, a system name on the wrong binary, a `watch` / `unsafe` mark |
| `NEW` | unannotated userland processes, bold red; `sug` or `sys?` is a hint |
| `SAFE` | every positive trust level, plus kernel threads |

- A zombie you annotated with a positive level leaves `WEIRD`: a dead process
  cannot act.
- `NEW` and `WEIRD` rows sit **under their real parents**, even `SAFE` ones.
  A safe parent may appear twice: a suspicious child never loses its context.
- A fold belongs to its band: folding `systemd` under `NEW` leaves it open
  under `SAFE`.

## Provider groups

`SAFE` is split by [provider](trust.md#provider), riskiest first:

1. `unlabelled`, `app`, `service`, `desktop`: open at start;
2. `derivative`, `distro`, `systemd`, `kernel`: folded, one line each with
   their count, memory and CPU.

The ancestors a whole group shares move into its header, read from the nearest
outwards. A parent from another group shows dim, as context:

```text
  ▾ app  (17) ∈ systemd ∈ systemd
     ▾ gnome-shell          2233   SAFE     desktop      (dim: context)
         firefox-bin      19889   SAFE     app
```

`Enter` on a header shows what the group means, its totals, the shared chain,
its trust levels and its heaviest processes.

## Kernel threads

A process with no executable, no `argv` and `kthreadd` as parent is a kernel
thread. It shows a dim `kernel`, never `NEW`, last in `SAFE`, folded by name
family:

```text
  ▾ kernel  (174)
       kthreadd                2
    ▸ kworker  (97)  generic work queues
    ▸ irq  (17)  hardware interrupt handlers, one per device line
```

A family name explains; it proves nothing. A kernel rootkit can call its
thread `kworker`, and then it also controls `/proc`. Auditing the kernel means
auditing its modules (`lsmod`).

## Frozen by default

The app starts **frozen**: one scan, then the timer pauses.

- `r` takes one fresh snapshot;
- `p` resumes the automatic refresh.

A stable view is what lets an agent and a human discuss one signature.
