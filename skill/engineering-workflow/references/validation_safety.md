# Validation Safety

Use this canonical reference before classifying or executing validation commands.

## Modes

### `read_only_verify`

Allow only inspection that does not execute repository-authored code, create files, change runtime state, use the network, load repository plugins, or run package-manager lifecycle scripts.

Examples include file reads, path inspection, safe text search, `git status --short`, `git diff`, `git diff --check`, and `git ls-files`.

Do not classify these as read-only:

- `make help`
- an arbitrary executable or repository script with `--help`
- project tests, linters, builds, or generators
- package-manager commands
- repo-authored shell scripts

### `disposable_copy_verify`

Run repo-authored tests, builds, linters, and other copy-only commands in a temporary copy with:

- a minimal credential-free environment
- a separate temporary home and temp directory
- network disabled or a command-specific offline wrapper
- bounded timeout
- captured exit status under an opaque command index and fingerprint, without raw command text or noisy secret-bearing output
- guaranteed cleanup

Preserve internal symlinks, but reject the run if a copied symlink resolves outside the disposable tree. When the host provides an enforceable sandbox, deny network access, writes outside the temporary root, and reads from the user's home outside that root. Without such a boundary, run only commands that are intrinsically offline and do not execute repository code, or require an explicit offline wrapper.

### `live`

Use only when mutation of the real target is explicitly authorized and belongs to the requested workflow. Validation authorization does not broaden product or operational scope.

## Token-Aware Classification

Parse a single command with `shlex` or an equivalent tokenizer. Reject malformed input and shell control syntax conservatively.

In read-only mode reject:

- `&&`, `||`, semicolons, newlines, and pipes
- redirects
- command substitution and backticks
- shell/environment expansion
- unknown executables
- hidden second commands
- a safe prefix followed by an unsafe suffix

Allowlist exact non-mutating Git subcommands and safe textual tools. Deny mutating Git subcommands even when the rest of the command looks harmless. Git pager, external-diff, text-conversion, and internal-exec options are live-only because configuration may launch helpers. For tools such as `find` and `sed`, reject their mutating/exec options, including GNU `find` output-file actions.

## Execution Boundary

Classification is not execution permission. A `copy_only_safe` result means the command may run only through the disposable-copy runner. Network-capable package commands require an explicit offline wrapper; a sanitized environment alone is not a network sandbox.

The only Python-module command exempt from an OS network guard is the exact recommended `python` or `python3 -m compileall .` shape, rewritten to the current interpreter with isolated module lookup (`-I`). Altered paths or arguments receive no exemption, and repository `compileall.py` must never shadow the standard library.

Never return or interpolate a caller-supplied command string in structured results, validation errors, logs, or reports. Use the opaque command index/fingerprint emitted by the runner.

Approvals and semantic judgment remain direct root-agent decisions. Do not bury them in a shell chain or programmatic loop.
