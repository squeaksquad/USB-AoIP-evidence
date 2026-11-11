# USB-AoIP evidence

The measurement record behind [USB-AoIP](https://github.com/squeaksquad/USB-AoIP):
harness results, bridge and owner logs, API snapshots and the analysers written
on the day, for every figure the project's `PROJECT_HANDOFF.md` cites.

Until 2026-11-10 this was the `outputs/` directory of the main repository, and
it keeps that directory's history. The handoff cites paths as `outputs/...`;
drop the `outputs/` prefix to find them here. To have them resolve in place,
clone this repository as `outputs/` inside a USB-AoIP checkout (the main
repository ignores that directory):

    git clone https://github.com/squeaksquad/USB-AoIP-evidence outputs

The measurement tools write new results into `outputs/` too; commit them here.

| Path | Contents |
|---|---|
| `latency/` | Round-trip, soak, noise-probe and capture evidence, one entry per run or campaign, named by label and UTC timestamp. |
| `dsp-verify/` | DSP compiler and engine verification runs. |
| `dsp-service/` | The 2026-09-11 DSP service review bundle and event captures. |
| `screenshots/` | Audio MIDI Setup channel-label screenshots. |

Naming in `latency/` is described in the main repository's `CLAUDE.md`. Four
analysers that are still in use moved to the main repository's
`tools/analysis/` (`zeros.py`, `gaps2.py`, `channel-zeros.py`,
`set-rate-one.py`); the rest stay beside the data they read. Scripts here that
call into the main repository name its layout before 2026-11-10 (tag
`layout-2026-11-01` there).

Licence: Apache-2.0, as the main repository.
