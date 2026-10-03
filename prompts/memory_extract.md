# omnis.prompt.memory_extract.v1

You extract revisable semantic memory from one Omnis event and its evidence. Return JSON only.
Do not include chain-of-thought. The worldline event itself is already preserved; extract only durable
interpretations that would be useful later.

Input:
- event: {{EVENT_JSON}}
- entities: {{ENTITIES_JSON}}
- existing_relevant_memory: {{MEMORY_JSON}}
- evidence_refs: {{EVIDENCE_JSON}}

Output schema:
{
  "assertions": [
    {
      "subject_id": "uuid",
      "predicate": "dotted.semantic.predicate",
      "object": {"type":"node|text|bool|i64|u64|f64","value":"..."},
      "confidence": 0.0,
      "valid_from_ns": 0,
      "valid_until_ns": null,
      "evidence_ids": ["..."]
    }
  ],
  "preferences": [
    {
      "value": "...",
      "scope_ids": ["uuid"],
      "confidence": 0.0,
      "evidence_ids": ["..."]
    }
  ],
  "expectations": [
    {
      "subject_id": "uuid",
      "predicate": "...",
      "expected_value": {"type":"...","value":"..."},
      "deadline_ns": null,
      "confidence": 0.0,
      "evidence_ids": ["..."]
    }
  ],
  "decisions": [
    {
      "selected": "...",
      "alternatives": ["..."],
      "reason_summary": "brief evidence-based explanation",
      "evidence_ids": ["..."]
    }
  ]
}

Rules:
- omit trivial/restatable event details with no durable value;
- every record needs real evidence_ids;
- do not overwrite contradictions; output the new interpretation and let graph rules relate it;
- explicit user statements may have confidence up to 1.0;
- inferred semantics must not exceed 0.9;
- do not create a preference from a single behavior unless the event explicitly states preference.
