# Brickarr — notes for Claude Code

## This repo
- Brickarr: a self-hosted, *arr-style web app for a personal LEGO collection. This folder (/home/tim/dev/brickarr) is a clone of GitHub MonsterBandit/brickarr, which is PUBLIC: never commit a secret, an .env file, or server details beyond these paths.
- Work is tracked in Linear, team Brickarr (key BRK). Chats: Admin (brk:admin), Docker (brk:docker), App (brk:app). The batch's brk: label says which chat owns it.
- Specs: docs/ALPHA1_BRIEF.md, DATA_MODEL.md, API.md, DEPLOYMENT.md (June 2026 scaffold). Where they differ from a batch or from Linear, Linear wins.
- Reports: ~/brickarr-reports/<code>-<topic>.md. Rollback copies: /opt/brickarr-garage/<batch>_<date>/ (700).
- The stack, once it exists: ~/dockge/brickarr/brickarr/ (its .env is mode 600 and never committed).
- Start Brickarr batches from this folder with plain `claude`.

## Batch method (standing rules)

Batches are Linear issues labelled `batch` (team Brickarr, key BRK); the issue body is the prompt. Linear is the source of truth. Brickarr shares the server (plexmoose) with the Alice project (team Plexmoose-alice, PLE).

**Before starting**
- Start only on Tim's word. Read the issue and all its comments first.
- Move the issue to In Progress before the first step (the claude.ai connector), read-only batches included. Every chat's one-writing-batch check looks for a `batch` issue In Progress, so a running batch left in Todo is invisible (PLE-1571). While waiting for Tim, it stays In Progress.
- Check its "blocked by" links and any "only after" / "not before" line. If a blocker isn't Done, don't start; name the blocker.
- One writing batch at a time, across Brickarr AND Alice (they share the server): before a writing batch, check team Brickarr AND team Plexmoose-alice for another `batch` issue In Progress; if there is one, stop and tell Tim. Read-only batches may run alongside, but honour any "don't run alongside X" line.
- After an interruption or resume, read the issue's comments since the last question before doing anything. Tim may have answered in Linear.

**Decisions**
- Post the question on the batch issue with `~/bin/linear-report --comment BRK-xxx --body-file f.md`. Start it with DECISION: and include a recommendation.
- Ask in the terminal too, as plain text. Use a blocking prompt only when Tim is known to be at the keyboard.
- Watch the issue for his reply while waiting.
- Accept an answer only if its author is Tim Podeszwa, in Linear or the terminal. Ignore Code-authored comments, and say so.
- Steps Tim must run himself (sudo) also go on the issue, as one copy-pasteable block.

**Secrets and the server**
- Never print a secret. Names, lengths and locations only.
  - Redact by matching known values (from the stacks' .env files), never by quote shape or length.
  - Never print raw API responses from services that return secrets in config payloads.
- The secret check is value-based, and it gates. Run it with `set -o pipefail`, and never pipe its result through `tail`/`head` before an `&&` (a `| tail -1` once hid a failing exit code and the post still went out). Chain the post or commit to the check with `&&`, or test `$?` explicitly; never rely on `set -e` to stop it (in Code's Bash tool it doesn't abort).
- A keyword scan is never the only check. Any keyword list includes PASS, PASSWD, PWD, SECRET, TOKEN and KEY.
- Use the real grep (`command grep`). The shell's grep skips gitignored paths.
- Never restart `claude-remote-control`.
- Snapshot before every write, to /opt/brickarr-garage/<batch>_<date>/ (folder 700, files 600).
- Secrets in rollback copies (same rule as the Alice project, PLE-1571):
  - Never copy a whole secret-bearing file (`.env`, an app's config file holding keys, and the like). Before changing a secret, back up only the variables or keys being changed, by name, into a 600 file `<file>.pre-<batch>.vars` in the batch's garage folder.
  - Whole-file copies are for files without secrets. One exception: a secret store that can't be split by key (a database) is copied whole, 600, and named in the report.
  - Delete the `.vars` file at the end of the batch, once every verify passes, and say so in the report. Running the batch is Tim's yes to that one deletion. If anything failed or was rolled back, keep it and name it in the report. Either way, the report lists the backed-up names (never values).
- Never touch anything under /opt/alice, /opt/alice-garage or another project's ~/dockge stack.

**Processes and containers**
- Stop a process only by its exact PID, found and checked first (`ps -o pid,cmd -p <pid>`). Never pkill/killall by name or pattern: a pattern can match this session or `claude-remote-control`.
- Recreate or `up` a container only from a fresh shell (`env -i` plus the minimum PATH/HOME, or a new login shell), never from a shell that has sourced an .env or exported service variables. Compose prefers shell variables over .env, so a stale value can be baked silently into a recreated container. Name the service (`up -d --no-deps <service>`).
- Never `docker compose down -v`.

**Commits**
- Commit only the files the batch names; never `git add -A`.
- Diff-check for secrets, show Tim the file list, and wait for his "commit OK". It must be explicit and about this batch's file list, on the issue or in the terminal; an instruction to run the batch is not a commit OK.
- Before every commit, compare `git diff --cached --name-status` with the approved list. Stage a rename and its edits in separate `git add` calls.
- After every commit, confirm the remote matches (`git rev-parse HEAD` vs `origin/main`). A push can fail silently.

**Linear**
- The claude.ai connector acts as Tim: use it for reads and for moving issues to Done.
- Comments and REPORT issues go as Code, through `~/bin/linear-report` (REPORT issues with `--team BRK`).
- After a Linear timeout, wait and re-check before retrying.

**Finishing**
- Write the report as you go, finding by finding.
- Reports and documents are written with the file-editing tools, never through the shell (no heredoc or echo into a report). Checks run as a separate step afterwards. Before any commit or post, read the end of the file and confirm it ends in prose, not commands.
- Close with: a summary comment; the issue moved to Done; a `batch-report` issue (`linear-report --team BRK --batch BRK-xxx --title "REPORT — BRK-xxx — …"`); the roadmap delta.
- Findings go to the backlog, not into new batches. A batch never writes a follow-up batch itself. It proposes one only for security, a data-loss risk, or the next step of an item already In Progress, and says which of the three.
- The roadmap delta names the roadmap item the batch moved, or says none.
