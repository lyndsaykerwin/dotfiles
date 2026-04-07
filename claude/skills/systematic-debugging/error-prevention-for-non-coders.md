# Error Prevention, Diagnostics & Debugging (For Non-Technical Users)

You are working with a beginner AI programmer. Projects and systems MUST be built so that errors are prevented where possible, diagnosed quickly when they occur, and fixable by a future Claude session that has zero prior context.

## Build for Visibility (The "Black Box" Rule)

Every script that runs for more than a few minutes must leave a clear trail of what happened inside it. A future session should be able to read the logs and understand exactly what broke, when, and why — without guessing.

**Structured logging is mandatory for any long-running script:**
- Use Python's `logging` module, not `print()`. Every message needs a timestamp, severity level (DEBUG/INFO/WARNING/ERROR), and the script name.
- Log to BOTH a file on disk (so you can read it after a crash) AND the console (so watchdogs and the user can see progress).
- Use `exc_info=True` on every `except` block that catches a real error. This captures the full traceback — the exact line of code that crashed. Without it, you only get "something broke" which is useless.
- Log files go in the project's data directory with timestamps in the filename (e.g., `crawl_2026-03-18_143000.log`). Never overwrite old logs.

**Per-operation tracking:**
- Log START and END for each unit of work (each record, each API call, each file processed) with: what it is, how long it took, and whether it succeeded.
- Maintain a failures file (JSON) listing every failed operation with: what failed, the error message, the full error type, and the system state (RAM, CPU) at failure time. This file must be actionable — you should be able to re-run just the failures.

**System health monitoring:**
- For scripts that use browsers, subprocesses, or heavy computation: log RAM usage, CPU, and thread count at regular intervals (every 25-50 operations).
- Log system health immediately after any crash — this is the single most valuable diagnostic data point.
- Use `psutil` for system metrics. If it's not in the project's requirements, add it.

## Prove It Works Small Before Running It Big

NEVER launch a long-running operation (more than ~50 iterations or ~10 minutes) without first proving the code works on a small test set. This is non-negotiable.

**The test-first protocol:**
1. Before any batch operation, run it on 3-5 records first with `--limit 3` or equivalent.
2. Inspect the output manually. Don't just check "did it finish without errors" — verify the actual output data looks correct.
3. If the script will run unattended (overnight, in background), also test: what happens when one record fails? Does it recover and continue, or does it crash the whole run? Simulate a failure intentionally.
4. Only after the small test passes should you proceed to the full run.

**What "test" means for different operations:**
- Data pipeline/crawl: Run 3-5 records, verify the output file has correct data, verify errors are caught and logged
- API batch calls: Run 1-2 calls, verify the response format, verify rate limit handling
- Database migrations: Run on a test/staging copy first, never directly on production data
- File transformations: Process 3 files, manually diff input vs output

## Fix the Root Cause, Not the Symptom

When an error occurs, do NOT immediately apply a patch and say "fixed." That pattern leads to multiple rounds of "I fixed it" -> same crash -> "I fixed it again" -> same crash.

**The debugging protocol:**
1. **Read the actual error first.** Read the full traceback, the log file, and any crash output. Do not guess at the cause.
2. **Form a hypothesis.** State it explicitly: "I think this crashed because X, and here's the evidence that supports that."
3. **Identify the root cause vs. the symptom.** A `TimeoutError` is a symptom. The root cause might be: the site is slow, the timeout is too short, zombie processes are consuming all RAM, or a previous operation didn't clean up properly. Fix the root cause.
4. **Verify the fix.** After applying a fix, reproduce the original failure condition and confirm it no longer fails. Do not just re-run the script and hope — deliberately test the specific scenario that broke.
5. **If you cannot reproduce the error or are uncertain about the cause, say so.** "I'm not sure what caused this — here are two possibilities and how we can tell which one it is" is infinitely more useful than "Fixed!" followed by another crash.

**Never claim a fix is working without evidence:**
- "I fixed the timeout error" is NOT acceptable. Instead: "I increased the timeout from 30s to 60s. I tested on the URL that was failing (example.com) and it now completes in 42s. Here's the log output showing it succeeded."
- If you can't test the fix right now (e.g., it only happens under load, or overnight), say so: "I applied a fix but I can't verify it until the next full run. Here's what to look for in the logs to confirm it worked."

## Design for Recoverability

Long-running operations WILL crash. Design for it.

- **Checkpoint frequently.** Save progress to disk every 25-50 operations, not just at the end. Use atomic writes (write to a temp file, then rename) so a crash mid-save doesn't corrupt the checkpoint file.
- **Make operations resumable.** When a script restarts, it should detect existing progress and pick up where it left off — not start over from record 1.
- **Separate "what's done" from "what failed."** Track completed records, failed records, and not-yet-attempted records as three distinct sets. A future session should be able to look at the state and know exactly what remains.
- **Clean up resources.** If your script launches browsers, subprocesses, or network connections, make sure they get cleaned up on both normal exit AND crash. Zombie processes from a crashed script will cause the next run to fail too.
