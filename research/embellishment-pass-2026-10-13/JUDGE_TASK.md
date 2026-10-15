# Judging, blind: the agent's task

You are a judge. For each text you are given, read its blind packet,
`research/embellishment-pass-2026-10-13/judge-blind/NAME.json`. It holds:
- `instructions`: how to judge;
- `prompt`: the original, the brief, and the anonymous candidates A to E;
- `schema`: the JSON your report must match.

Write your report as JSON to `research/embellishment-pass-2026-10-13/judge-blind/NAME.report.json`, following the
instructions exactly: for every candidate and every criterion, the evidence first (quoting the candidate
verbatim), then the score; then its problems, each with a verbatim quote; then the rankings.

Work from `/workspace/aussiefy`. Check each report with `.venv/bin/python
research/embellishment-pass-2026-10-13/check_report.py NAME`, which prints "ok" or what to fix (a quote that isn't
verbatim, a missing field), and fix it until it says ok.

**Stay blind.** Open nothing but the packets and your reports: not `research/embellishment-pass-2026-10-13/texts/`,
not the first pass's directory, not the yarn notes. Judge each text on its own. Don't edit any other file.

When you're done, reply with one line per text: its name and "ok".
