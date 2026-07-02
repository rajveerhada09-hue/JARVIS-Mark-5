# CODING_RULES.md

---

# JARVIS MARK 5

Official Development Rules

Version : Mark 5

These rules are mandatory.

Every AI assistant and every human contributor must follow them.

Violating these rules creates technical debt and unstable architecture.

---

# RULE 1

Never rewrite working code.

If a module already works correctly,

DO NOT replace it.

Improve only what is necessary.

Minimal change is always preferred.

---

# RULE 2

Never change folder architecture.

Folders are considered stable unless Rajveer explicitly requests architectural changes.

---

# RULE 3

One module.

One responsibility.

Never combine multiple systems into one file.

Bad

Brain handles automation.

Good

Brain decides.

Automation executes.

---

# RULE 4

Never duplicate logic.

If functionality already exists,

reuse it.

Never create another version.

---

# RULE 5

Always check existing code before writing new code.

Search first.

Reuse second.

Write new code last.

---

# RULE 6

Never invent filenames.

Never invent imports.

Never invent folders.

Always verify they already exist.

---

# RULE 7

Never guess APIs.

Read implementation first.

If implementation is unavailable,

stop and ask.

---

# RULE 8

Never fabricate function names.

Bad

brain.run()

Good

Use the actual implementation inside the project.

---

# RULE 9

Never modify unrelated modules.

If fixing voice,

do not modify memory.

If fixing browser,

do not modify kernel.

---

# RULE 10

Kernel must remain lightweight.

Kernel coordinates.

Kernel never thinks.

Kernel never automates.

Kernel never stores memory.

---

# RULE 11

Brain performs reasoning only.

Brain never

opens browser

clicks mouse

moves keyboard

plays spotify

executes automation

---

# RULE 12

Automation never communicates with LLM.

Automation receives commands.

Automation executes commands.

Nothing more.

---

# RULE 13

Memory stores information only.

Memory never generates responses.

Memory never reasons.

---

# RULE 14

Voice handles audio only.

Voice never performs reasoning.

Voice never controls automation.

---

# RULE 15

Never hardcode values.

Use

utils/config.py

or

jarvis_config.json

---

# RULE 16

Every configurable value belongs inside configuration.

Examples

Voice Volume

Spotify Volume

Wake Word

Timeout

Animation Speed

API Keys

Device Names

All belong inside configuration.

---

# RULE 17

Every new module must contain a header.

Example

PROJECT

FILE

PATH

PURPOSE

LAST UPDATED

---

# RULE 18

Always preserve backward compatibility.

New code must not break existing modules.

---

# RULE 19

When editing code,

modify the minimum number of lines.

Avoid unnecessary rewrites.

---

# RULE 20

Always mention affected files.

Every response should specify

Files to modify

Files to create

Files to leave untouched

---

# RULE 21

Before adding a new file,

verify whether an existing file can handle the feature.

Avoid unnecessary files.

---

# RULE 22

Never create temporary architecture.

Everything added should have a long-term purpose.

---

# RULE 23

Never delete existing functionality unless explicitly requested.

---

# RULE 24

Comments should explain WHY.

Not WHAT.

Bad

# increment i

Good

# Move to next memory candidate

---

# RULE 25

Logging is mandatory.

Every important system should log

startup

shutdown

errors

warnings

critical events

---

# RULE 26

Never expose secrets.

Never hardcode

API Keys

Passwords

Tokens

Environment Variables

Use .env only.

---

# RULE 27

Error handling is mandatory.

Every subsystem should fail gracefully.

Never crash the whole application.

---

# RULE 28

Documentation must remain synchronized.

Whenever architecture changes,

update

PROJECT_ARCHITECTURE.md

CURRENT_STATUS.md

CHANGELOG.md

---

# RULE 29

Never assume repository structure.

Always verify before importing.

---

# RULE 30

Code quality priorities

1 Stability

2 Readability

3 Maintainability

4 Performance

5 Features

Never sacrifice stability for features.

---

# RULE 31

Project Evolution Rule

The project must evolve in stages.

Current stage must become stable before adding new systems.

No exceptions.

---

# RULE 32

AI Assistant Development Rule

Before writing code,

AI assistants must read

PROJECT_ARCHITECTURE.md

FOLDER_STRUCTURE.md

CODING_RULES.md

CURRENT_STATUS.md

Only then should implementation begin.

---

# RULE 33

Golden Rule

If uncertain,

do not invent.

Read the code.

Understand the architecture.

Then modify the project.

---

End of Coding Rules.
