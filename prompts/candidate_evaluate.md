# omnis.prompt.candidate_evaluate.v1

Evaluate an Omnis self-evolution candidate against the supplied baseline evidence. Return JSON only.
Do not expose chain-of-thought.

Input:
- target: {{TARGET}}
- baseline_metrics: {{BASELINE}}
- candidate_metrics: {{CANDIDATE}}
- test_results: {{TESTS}}
- replay_results: {{REPLAY}}
- authority_findings: {{AUTHORITY}}

Output schema:
{
  "passes_build_tests": false,
  "success_regression_fraction": 0.0,
  "resource_cost_change_fraction": 0.0,
  "success_improvement_fraction": 0.0,
  "authority_violation": false,
  "reproducible": false,
  "eligible_for_promotion": false,
  "evidence_ids": ["..."]
}

Eligibility must exactly apply docs/ONTOLOGY_V0.md self-evolution gates; do not invent additional
promotion criteria.
