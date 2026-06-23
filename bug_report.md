# Pretty Good AI — Voice Assessment Bug Report

Document issues found while testing **+1-805-439-8008**.

After each completed call, the analyzer appends findings here automatically when issues are detected.
You can also add manual entries.

## Example entry

## Bug: Agent confirms appointment for Sunday without checking office hours
- **Severity:** High
- **Call:** call-09-sunday_edge.txt (call-09-sunday_edge), ~1:10
- **Recording:** call-09-sunday_edge.mp3
- **Details:** Patient asked for Sunday at 10am; agent confirmed without stating weekend closure.
- **Why it matters:** Patient may arrive when the office is closed.
- **Expected:** Agent should explain weekend closure and offer next weekday slot.
