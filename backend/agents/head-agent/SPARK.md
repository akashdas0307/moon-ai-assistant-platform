# SPARK Heartbeat Configuration

> **⚠️ IMMUTABLE FILE:** This file defines the SPARK heartbeat system configuration.
> The agent reads this file but NEVER modifies it. Changes must be made manually by users.

## About SPARK

SPARK (Systematic Periodic Awareness & Review Keeper) is an autonomous heartbeat system
that periodically awakens the agent to check for pending tasks without requiring user
interaction. This enables the agent to maintain awareness of ongoing objectives and
self-initiate task continuations when needed.

## Configuration

### Heartbeat Interval
```yaml
interval_minutes: 15
```
**Description:** How often SPARK wakes up to check the NOTEBOOK.md for pending tasks.
**Default:** 15 minutes
**Range:** 5-60 minutes (lower = more frequent checks, higher token usage)

### Token Budget
```yaml
max_check_tokens: 500
```
**Description:** Maximum tokens allowed per SPARK check to keep costs low.
**Default:** 500 tokens
**Purpose:** Ensures SPARK checks are cheap (only reads NOTEBOOK.md + archived items)

### Log Settings
```yaml
log_directory: spark_logs
log_retention_days: 7
log_format: "{timestamp} | {status} | {action}"
```
**Description:** Configuration for SPARK activity logging.
**Logs Include:**
- Timestamp of each heartbeat
- Status (OK = no action needed, ACTION = pending task found)
- Description of action taken or pending item detected

### Enabled Status
```yaml
enabled: true
```
**Description:** Whether SPARK heartbeat is active.
**Options:** true (enabled) | false (disabled)

## How SPARK Works

1. **Wake Up:** Timer triggers based on `interval_minutes`
2. **Read Context:** Loads last 15 lines of NOTEBOOK.md and archived_notebook.md
3. **Check for Pending Tasks:** Looks for `[PENDING]` markers
4. **Evaluate:** Determines if any pending task needs immediate attention
5. **Act or Sleep:**
   - If action needed: Wakes main agent with minimal context
   - If no action needed: Logs "OK" and goes back to sleep

## SPARK Logging Example

```
2026-02-16T14:00:00Z | OK | No pending tasks found
2026-02-16T14:15:00Z | OK | No pending tasks found
2026-02-16T14:30:00Z | ACTION | Found pending task: "Follow up on project report"
2026-02-16T14:45:00Z | OK | Previous task completed
```

## Important Notes

- **Immutability:** This file should rarely change. SPARK configuration is intentionally stable.
- **Token Efficiency:** SPARK is designed to be extremely cheap (<500 tokens per check)
- **No Heavy Lifting:** SPARK only identifies pending work; the main agent does the actual work
- **Audit Trail:** All SPARK activity is logged for transparency and debugging

## Modification Instructions

If you need to change SPARK settings:
1. Stop the backend server
2. Edit this file manually
3. Restart the backend server
4. Verify changes in `spark_logs/` output

**Do not** modify this file while the agent is running.
