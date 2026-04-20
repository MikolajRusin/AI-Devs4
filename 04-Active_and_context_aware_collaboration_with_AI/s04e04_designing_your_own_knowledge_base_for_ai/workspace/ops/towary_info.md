---
type: schema
directory: /towary
owner: agent
---

# /towary directory

## Purpose

Each file represents one sellable item. ONE file per unique item name.
The file lists ALL cities that sell that item.

## File naming

- Filename = item name, singular nominative, lowercase, no Polish characters
- No file extension
- One file per item regardless of how many cities sell it

Example: łopata → `lopata`

## File content

One markdown link per selling city, one per line. Use the global unique filename as both display text and href (no path prefix needed).

Format for item sold by one city:
```
[cityfilename](cityfilename)
```

Format for item sold by multiple cities:
```
[cityfilename1](cityfilename1)
[cityfilename2](cityfilename2)
[cityfilename3](cityfilename3)
```

Example — łopata sold by Brudzewo and Puck, file `/towary/lopata`:
```
[brudzewo](brudzewo)
[puck](puck)
```

## Source

Extract seller-to-item mappings from: workspace/notes/transakcje.txt
Format of each line: Seller -> item -> Buyer
The SELLER (left side) is the city that offers the item.
Collect ALL sellers per item and list them all in one file.

## Rules

- Item name in filename must be singular nominative (e.g. "kilof" not "kilofy")
- No Polish characters in filename or content (ą→a, ć→c, ę→e, ł→l, ń→n, ó→o, ś→s, ź→z, ż→z)
- ONE file per item — do NOT create separate files per seller
