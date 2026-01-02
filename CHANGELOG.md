# Changelog

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
