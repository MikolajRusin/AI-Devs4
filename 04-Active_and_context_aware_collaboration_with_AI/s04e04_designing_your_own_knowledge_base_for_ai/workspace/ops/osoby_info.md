---
type: schema
directory: /osoby
owner: agent
---

# /osoby directory

## Purpose

Each file represents one person responsible for trade in a city.
One person per file, one file per city.

## File naming

- Filename = first name + surname concatenated, ALL LOWERCASE, no Polish characters, no spaces, no separators
- No file extension
- Allowed pattern: `^[a-z0-9_]+$`

Example: Marta Frantz → `martafrantz`
Example: Rafał Kisiel → `rafalkisiel`

## File content

First line: the person's full name exactly as known (preserve Polish characters — the API matches by name).
Second line: a markdown link to their city file using the global unique filename.

Format:
```
Full Name
[cityfilename](cityfilename)
```

Example — file path `/osoby/martafrantz`, content:
```
Marta Frantz
[darzlubie](darzlubie)
```

## Source

Extract person-to-city assignments from: workspace/notes/rozmowy.txt
Each conversation entry mentions a person and the city they represent or manage.
Use full name (first name + surname).
