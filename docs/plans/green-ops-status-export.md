# Standing Windows status export

The repository progress tracker is authoritative. The Windows file is a one-way
snapshot, never a source to merge back into this repository.

Read the external instructions before refreshing:
`/mnt/c/Users/thite/Documents/Codex/2026-11-10/superpowers-plugin-superpowers-openai-curated-remote/green-ops-status-export-instructions.md`.
Destination:
`/mnt/c/Users/thite/Documents/Codex/2026-11-10/superpowers-plugin-superpowers-openai-curated-remote/green-ops-ubuntu-status.md`.

Refresh after each verified milestone/local commit, before requesting user input,
and before stopping or leaving an interruption handoff. Include timestamp/timezone,
repository path, current task/status, full branch/HEAD and short branch status,
latest verified test command/result and tested state, milestone changes, metrics/
units/provenance/groups, findings/assumptions/blockers, next action/user action,
push/publication status and relative tracker/result/review/handoff paths.
Distinguish unchecked later changes from verified code. Publish UTF-8 by fully
writing a temporary sibling and atomically replacing the destination. If external
write permission is unavailable, retain a repository report and state the blocker.
Never export credentials/tokens. Do not start another agent or a polling service.

Export success does not imply the Windows chat has read it. That chat reads it
on the user's next request; no automatic notification or continuous monitoring.
