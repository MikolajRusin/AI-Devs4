---
type: process
status: active
owner: agent
---

# Task: filesystem

## Goal

Read Natan's notes and build a structured virtual filesystem via the /verify/ API.
The filesystem must contain exactly three directories: /miasta, /osoby, /towary.

## Input

All source notes are in workspace/notes/:
- ogłoszenia.txt — what each city needs (demands)
- rozmowy.txt — who is responsible for trade in each city
- transakcje.txt — which city sells which item (format: Seller -> item -> Buyer)

## Steps

1. Call filesystem(action="help") to learn API limits and naming rules
2. Read all three note files and the three schema docs
3. Call filesystem(action="reset") — do this FIRST, before any other filesystem call
4. Create the three root directories with separate calls: createDirectory /miasta, createDirectory /osoby, createDirectory /towary
5. Send all createFile operations in a single batch call
6. Call filesystem(action="done") to submit for verification

## Directory contracts

- [miasta_info.md](miasta_info.md) — how /miasta files must look
- [osoby_info.md](osoby_info.md) — how /osoby files must look
- [towary_info.md](towary_info.md) — how /towary files must look

## API filename rules (confirmed from help)

- Allowed pattern: `^[a-z0-9_]+$` — only lowercase letters, digits, underscores
- No uppercase, no dots, no spaces, no Polish characters in filenames
- Filenames are globally unique across all directories

## Link format

Since filenames are globally unique, reference any file by name only — no path needed:
```
[displaytext](filename)
```
Example: to link to /miasta/domatowo use `[domatowo](domatowo)`

## Rules

- No Polish characters in filenames (ą→a, ć→c, ę→e, ł→l, ń→n, ó→o, ś→s, ź→z, ż→z)
- Item names are singular nominative (e.g. "kilof" not "kilofy", "lopata" not "lopaty")
- Only markdown syntax accepted in file content; links must point to existing files
