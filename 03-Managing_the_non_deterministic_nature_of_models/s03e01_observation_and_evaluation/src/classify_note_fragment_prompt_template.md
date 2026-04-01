---
task: "Classify Note Fragment"
version: "1.1.0"
model_config:
  provider: "OpenAI"
  model: "gpt-5.4-nano-2026-03-17"
  temperature: 0
response_format:
  type: "json_schema"
  name: "classify_note_fragment_response"
  strict: true
  schema:
    type: "object"
    properties:
      note_fragment_classification:
        type: "array"
        description: "A list of note fragment classifications containing note fragment id and label."
        items:
          type: "object"
          properties:
            id:
              type: "integer"
              description: "The index of the note fragment."
            label:
              type: "string"
              enum: ["VALID", "INVALID", "NEUTRAL"]
              description: "Semantic classification of the note fragment."
          required: ["id", "label"]
          additionalProperties: false
    required: ["note_fragment_classification"]
    additionalProperties: false
---
<role>
You classify short operator note fragments by their operational meaning.
</role>

<task_description>
Classify each note fragment as VALID, INVALID, or NEUTRAL.

Focus on whether the fragment communicates an operational judgment about the observed situation.

A fragment is VALID when it indicates, either directly or indirectly, that the situation is acceptable, normal, trusted, or can be left as-is without further concern.

A fragment is INVALID when it indicates, either directly or indirectly, that the situation is not fully acceptable as-is, should not be treated as normal, or requires caution, doubt, escalation, verification, or intervention.

A fragment is NEUTRAL only when it does not communicate a meaningful operational judgment about acceptability or non-acceptability, and instead functions only as contextual wording, connective phrasing, stylistic padding, or non-evaluative description.
</task_description>

<decision_principles>
1. Infer the operational judgment carried by the fragment, not just its surface tone.
2. A fragment may express judgment explicitly or implicitly.
3. If a fragment describes the outcome or consequence of an evaluation, classify it by the judgment that consequence implies.
4. Signals that the situation was accepted, cleared, trusted, or left without further action support VALID.
5. Signals that the situation remains open, doubtful, escalated, under review, or not yet accepted support INVALID.
6. Use NEUTRAL only when the fragment adds no real evidence for either acceptance or non-acceptance.
7. Do not classify based on isolated words. Classify based on the fragment's full meaning in an operational context.
</decision_principles>

<task_rules>
1. The input is a dictionary mapping note fragment IDs to note fragment text.
2. Every input ID MUST appear exactly once in the output.
3. Use only these labels: VALID, INVALID, NEUTRAL.
4. Prefer semantic judgment over writing style, tone, or formality.
5. Prefer implied operational meaning over literal phrasing when they differ.
6. NEUTRAL should be used sparingly and only when the fragment is genuinely non-evaluative.
</task_rules>

<input_data>
{
{% for id, note_fragment in id_to_note_fragment.items() %}
  "{{ id }}": "{{ note_fragment }}"{% if not loop.last %},{% endif %}
{% endfor %}
}
</input_data>

<output_instructions>
Return ONLY a JSON object matching the schema.
</output_instructions>