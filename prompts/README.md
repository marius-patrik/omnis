# OmnisAgent prompt registry

These files are canonical first-party generative prompt templates for v0.

Rules:

- prompt file bytes are versioned architecture inputs;
- every model invocation records the BLAKE3 ArtifactId of the exact expanded prompt/template;
- implementations do not rewrite prompt wording locally;
- template placeholders are filled with canonical JSON serialization of the referenced structured
  values;
- provider adapters may translate message roles/transport, but not semantic prompt content;
- model outputs are parsed against the output schema described in the template; invalid output is one
  retry with a fixed schema-error suffix, then a typed model failure.

Fixed retry suffix:

```text
Your previous response did not match the required JSON schema. Return only one valid JSON value that
matches the schema exactly. Do not add commentary.
```

The templates do not request hidden chain-of-thought; they request only action-relevant structured
outputs and evidence references.
