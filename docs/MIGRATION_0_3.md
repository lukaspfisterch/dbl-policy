# Migration to 0.3.0

Status: Working draft
Date: 2026-03-14

## Goal

Move `dbl-policy` from the mixed `contract + starter pack` shape of `0.2.2`
to a clear contract package that can serve as the foundation for
`dbl-policy-gates`.

## Scope

`0.3.0` should complete the contract cleanup. It should not try to ship the
gate algebra itself.

## Work Items

### 1. Contract surface

- keep `PolicyContext`, `PolicyDecision`, `DecisionOutcome`, `PolicyId`,
  `PolicyVersion`, and `TenantId` as the public contract core
- keep `decide_safe` as the recommended contract entrypoint
- keep `decision_to_dbl_event` as the DBL bridge
- review public exports in `src/dbl_policy/__init__.py` for contract-only focus

### 2. Documentation cleanup

- describe `dbl-policy` primarily as protocol and bridge
- mark the removed `dbl_policy.policies` package as superseded pre-alignment
  material
- make `docs/ARCHITECTURE.md` and `docs/dbl_policy_contract.md` the normative
  reading order
- remove wording that implies `dbl-policy` is the long-term policy algebra

### 3. Legacy package handling

- keep the removal explicit in docs and changelog
- do not restore the old starter pack under compatibility pressure
- use git history if the old material must be consulted

### 4. Gateway alignment

- ensure the gateway adapter preserves JSON-safe authoritative inputs
- prefer contract-safe evaluation over adapter-local validation logic
- keep gateway changes minimal and boundary-focused

### 5. Test realignment

- add tests that confirm structured JSON-safe inputs survive into
  `PolicyContext`
- keep tests for invalid deterministic inputs such as `bytes` and `float`
- verify `decide_safe` remains the stable fallback for invalid input and
  evaluation errors

### 6. Release discipline

- treat `0.3.0` as a contract-level release
- call out that policy-definition behavior changes for identical inputs are
  breaking changes
- document that `dbl-policy-gates` will target the `0.3.x` contract line

## Out of Scope

- no YAML or declarative policy format
- no rule engine
- no second reason-code system
- no gate algebra implementation inside `dbl-policy`
- no gateway redesign beyond adapter alignment

## Exit Criteria

`dbl-policy 0.3.0` is ready when:

- the package reads clearly as contract, not engine
- gateway boundary handling matches the contract
- legacy starter-pack material is explicitly non-canonical
- the package is a stable base for `dbl-policy-gates 0.1.0`
