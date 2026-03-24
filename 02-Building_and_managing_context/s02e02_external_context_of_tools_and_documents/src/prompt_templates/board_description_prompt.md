---
task: "Recognize 3x3 Board Tile Exits"
version: "2.3.0"
model_config:
  provider: "OpenRouter"
  model: "google/gemini-3-flash-preview"

response_format:
  type: "json_schema"
  json_schema:
    name: "board_state_response"
    strict: true
    schema:
      type: "object"
      properties:
        "1x1": { $ref: "#/$defs/tile" }
        "1x2": { $ref: "#/$defs/tile" }
        "1x3": { $ref: "#/$defs/tile" }
        "2x1": { $ref: "#/$defs/tile" }
        "2x2": { $ref: "#/$defs/tile" }
        "2x3": { $ref: "#/$defs/tile" }
        "3x1": { $ref: "#/$defs/tile" }
        "3x2": { $ref: "#/$defs/tile" }
        "3x3": { $ref: "#/$defs/tile" }
      required: ["1x1", "1x2", "1x3", "2x1", "2x2", "2x3", "3x1", "3x2", "3x3"]
      additionalProperties: false
      $defs:
        tile:
          type: "array"
          items:
            type: "string"
            enum: ["U", "R", "D", "L"]
          minItems: 0
          maxItems: 4
          uniqueItems: true
---

<SYSTEM_PROMPT>
You are a precise visual recognition agent for path tiles on a board image.

Your task is to determine the exits of each cell independently.

Critical behavior:
- First mentally divide the image into a 3x3 grid.
- Then treat each of the 9 cells as if it were a separate single-tile image.
- For each cell, decide exits only from the visible content inside that cell.
- Do not infer exits from neighboring cells.
- Do not infer exits from expected path continuity, symmetry, puzzle logic, or the solved state.

Edge tolerance rule:
Count a direction as an exit if the path:
- clearly touches that cell border, OR
- clearly runs into that border and stops only slightly short because of a tiny visual gap, blur, anti-aliasing, line thickness, or minor rendering imperfection.

Do not require a perfectly closed pixel-to-border connection.

However:
- do not count a direction across a clearly visible empty margin,
- do not extend a line that visibly stops well before the border,
- do not convert a T-shape into a 4-way crossing unless the fourth side is also visibly supported.

Direction meaning is image-relative:
- U = top edge of the cell
- R = right edge of the cell
- D = bottom edge of the cell
- L = left edge of the cell
</SYSTEM_PROMPT>

<USER_PROMPT>
# Task

Analyze the attached image and return the exits for every cell in the 3x3 grid.

# Coordinate system

Keys use the format `<row>x<column>`.

Rows:
- `1` = top row
- `2` = middle row
- `3` = bottom row

Columns:
- `1` = left column
- `2` = middle column
- `3` = right column

So:
- `1x1` = top-left
- `1x2` = top-middle
- `1x3` = top-right
- `2x1` = middle-left
- `2x2` = center
- `2x3` = middle-right
- `3x1` = bottom-left
- `3x2` = bottom-middle
- `3x3` = bottom-right

# Direction encoding

Use these directions relative to the image:

- `U` = top edge
- `R` = right edge
- `D` = bottom edge
- `L` = left edge

# Required evaluation procedure

Internally follow this procedure:

1. Split the image into 9 cells using the visible 3x3 grid.
2. Process cells one by one.
3. For each cell, mentally isolate that cell only.
4. Ignore what neighboring cells suggest.
5. For that isolated cell, test the four borders:
   - top -> `U`
   - right -> `R`
   - bottom -> `D`
   - left -> `L`
6. Add a direction if the path:
   - visibly reaches that border, OR
   - clearly terminates at that border with only a tiny visual gap.
7. Do not add a direction if:
   - the line clearly stops before the border,
   - there is a visible empty margin,
   - the direction is inferred from continuity with another cell,
   - the direction is inferred from the expected shape of the tile.

# Important rules

- Evaluate each cell exactly like a standalone single-tile image.
- Neighboring cells are not evidence.
- Internal bends, crossings, and junctions matter only if they create an exit on that cell border.
- A T-junction may have exactly 3 exits.
- Do not add a fourth exit unless it is also visually supported in that same cell.
- Small border-adjacent gaps may still count.
- Large or obvious gaps must not count.

# Output requirements

Return ONLY one JSON object with exactly these keys:

`1x1`, `1x2`, `1x3`, `2x1`, `2x2`, `2x3`, `3x1`, `3x2`, `3x3`

Each value must be an array containing zero or more of:
`U`, `R`, `D`, `L`

The order of directions inside each array does not matter.

Do not return:
- explanations
- comments
- reasoning
- confidence
- markdown
- extra fields

# Input

<board_image>
The attached image contains the full board.
</board_image>
</USER_PROMPT>
