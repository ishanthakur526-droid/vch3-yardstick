# Yardstick

A stock and ordering planner that runs on what the site actually uses.

Built at Vibe Coders Hackathon 3 (Kolkata, 21 Nov 2026) for Lumino Industries' problem statement **"1,700 Poles"**: a fixed supply plan kept sending material while the site used far less, and the surplus sat idle in a yard.

## What it does (built today, in this order)
1. **See it.** For every item and every godown, month by month: what came in, what went to contractors, what the site actually used, and what sat idle.
2. **Plan it.** Replays the project month by month. Each month it sees only what was known up to that date, and says what to order now (because of lead time), what to hold and what to move from another godown. Then it puts its plan next to what really happened: how much less stock would have sat idle, and what shortages the plan would have caused.
3. **Match the sets.** A parent item needs its child items in the right ratio. Flags every month where a set is out of balance, in any godown.

## Data
The project data belongs to Lumino Industries. It is not in this repo in readable form: the app reads a local copy during development, and the live app reads an encrypted bundle whose key is kept in the host's secrets.
