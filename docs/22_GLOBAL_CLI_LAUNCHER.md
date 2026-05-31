# Global CLI Launcher

Date: 2026-05-31

## Goal

Make SlyPilot runnable as a global terminal command:

```bash
slypilot
```

## Recommended launcher

Version the launcher in the repository:

```bash
bin/slypilot
```

Then expose it through a symlink in a directory on `PATH`, for example:

```bash
ln -s /Users/hakimradi/Nextcloud/SlyProjet/SlyPilot/bin/slypilot ~/.local/bin/slypilot
```

## Behavior

- `slypilot` starts interactive mode
- `slypilot "prompt"` runs the prompt directly
- `slypilot --dry-run "prompt"` prints the generated packet
- `slypilot --live-run "prompt"` sends the packet to the provider

## Why this approach

- the launcher stays versioned
- the project path is explicit
- the terminal entry point stays simple
- the core architecture is unchanged

## Optional alias

`slyagent` may be added later as a symlink if the product layer needs it.

For V1.1, the preferred command is still `slypilot`.

## Risks

- `PATH` not configured
- launcher symlink missing
- hard-coded project path must stay valid

## Validation

- `slypilot --help` works
- `slypilot "prompt"` works
- `slypilot --dry-run "prompt"` works
- `slypilot --live-run "prompt"` works
- the command is available from outside the project directory when the symlink is installed
