---
type: schema
directory: /miasta
owner: agent
---

# /miasta directory

## Purpose

Each file represents one city that appears in Natan's notes.
The file content describes what that city needs (its demands), extracted from ogłoszenia.txt.

## File naming

- One file per city
- Filename = city name in lowercase, no Polish characters, no spaces (use underscore if needed)
- No file extension

Example: Domatowo → `domatowo`

## File content

A flat JSON object ONLY — no markdown, no headers, no links, nothing else.
Keys = item name (singular nominative, lowercase, no Polish characters).
Values = integer quantity (no units).

Example:
```
{"makaron":60,"woda":150,"lopata":8}
```

## Source

Extract city needs from: workspace/notes/ogłoszenia.txt
Each announcement block describes one city and lists items with quantities.
