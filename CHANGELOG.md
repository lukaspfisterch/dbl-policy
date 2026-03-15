# Changelog

## [0.3.0] - 2026-03-14

- Freeze the root package surface around the contract API only:
  `Policy`, `PolicyContext`, `PolicyDecision`, `decide_safe`, `bridge`,
  `validation`
- Move root-level helper imports such as `DecisionOutcome`, `PolicyId`,
  `PolicyVersion`, `TenantId`, and `decision_to_dbl_event` out of the public
  package namespace
- Remove the pre-alignment `dbl_policy.policies` starter pack from the active
  package
- Add explicit architecture and migration documents for the contract/algebra
  split
- Keep `allow_all` and `deny_all` as explicit helper modules, not root exports

## [0.2.2] - 2026-01-02

- Add deterministic starter policy pack with composed allow/deny rules
- Introduce centralized policy config for allowlists and caps
- Tighten PolicyContext allowed keys to minimal starter set (+ extensions)
- Align builtin policy versions and docs with 0.2.2

## [0.2.1] - 2026-01-02

- Documentation and test hygiene
- Update contract to v0.2.0 with strict Mapping requirement
- Prescriptive bridge comments
- Synchronize builtin policy versions
- Reject str-subclass mapping keys (strict key typing)
- Add EVALUATION_ERROR reason code for policy evaluation failures

## [0.2.0] - 2026-01-02

- Enforce JSON-safe deterministic inputs (reject floats)
- Input whitelisting for PolicyContext
- Embed policy identity/lineage in decision events
- Transition to Mapping for DECISION.data

## [0.1.0] - 2025-12-26

- Initial policy contract and minimal API
- Deterministic PolicyContext and PolicyDecision types
- Decision to dbl-core DECISION event helper
