# Validation Safety

Validation must respect the active safety mode.

## Modes

- `read_only_verify`
  - no writes to the live target repo
  - only `read_only_safe` checks
- `disposable_copy_verify`
  - side-effectful checks may run in a temporary copy
- `live`
  - allowed only when mutation is already authorized

## Command Classes

- `read_only_safe`
  - existence checks
  - path or link lint
  - placeholder scans
  - `--help` style probes that do not write artifacts
- `copy_only_safe`
  - commands that may create bytecode, caches, temp reports, or lockfiles
  - `python -m compileall`
- `live_only`
  - commands that mutate tracked files or runtime state in the real repo

When a command can plausibly create `__pycache__`, cache directories, or generated files, it is not `read_only_safe`.
