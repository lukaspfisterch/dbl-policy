# Architecture

Status: Draft for review
Date: 2026-03-14
Applies to: `dbl-policy` transition from `0.2.2` to `0.3.0`

## Purpose

This document defines the target architecture for policy in the DBL stack after
the theory re-grounding aligned `dbl-gateway` with the EWN/DBL axioms.

The immediate goal is to separate three concerns that are currently too close
together:

- `dbl-policy` as protocol and contract surface
- `dbl-policy-gates` as deterministic gate algebra
- domain policies as root-level assemblies for tenant or product use cases

This split preserves the current strengths of `dbl-policy` while removing the
structural pressure that pushes it toward a rule engine.

## Architectural Position

The target stack is:

```text
execution-without-normativity
    -> dbl-core
    -> dbl-policy
    -> dbl-policy-gates
    -> domain policies
```

Interpretation:

- `dbl-core` owns event mechanics and canonicalization.
- `dbl-policy` owns the protocol for deterministic decisions.
- `dbl-policy-gates` owns the primitive operations used to build governance
  functions.
- domain policies own business meaning, versioning, and release discipline.

## Problem Statement

`dbl-policy 0.2.2` already contains the right contract core, but it also
contains a starter policy pack that predates the current theory alignment.

That creates three tensions:

1. The `Policy` protocol currently expects each policy object to carry
   `policy_id` and `policy_version` and to emit a complete `PolicyDecision`.
2. The old starter pack appears central in the README even though it is not the
   intended long-term architecture.
3. The gateway adapter currently narrows authoritative inputs more than the
   policy contract requires.

These tensions are manageable, but they should not become the basis for the
next layer.

## Target Model

### 1. `dbl-policy` becomes a contract package

`dbl-policy` should own only the protocol needed to evaluate and bridge
deterministic decisions:

- `PolicyContext`
- `PolicyDecision`
- `DecisionOutcome`
- `PolicyId`
- `PolicyVersion`
- `TenantId`
- validation and canonicalization
- `decide_safe`
- bridge into DBL DECISION events

This package is the normative contract surface, not the policy algebra.

### 2. `dbl-policy-gates` becomes the algebra package

`dbl-policy-gates` should own:

- atomic gates
- combinators
- deterministic `describe()`
- deterministic `describe_digest()`
- structured reason detail generation

The closure rule changes here:

```text
Gate + Gate -> Gate
```

Not:

```text
Policy + Policy -> Policy
```

That distinction matters. If every inner node must satisfy the outer policy
protocol, an evaluator layer reappears implicitly. The gate tree then starts to
behave like a rule engine.

### 3. Domain policies become root wrappers

A domain policy should be the only object that carries:

- `policy_id`
- `policy_version`

The root wrapper owns release identity and produces the final
`PolicyDecision`. The gate tree beneath it is structure, not identity.

Target shape:

```text
RootPolicy
    -> Gate tree
```

This preserves the invariant:

```text
identity on root only
```

## Invariants

The following invariants should govern the redesign.

### INV-ARCH-1: DECISION remains the only normative output

Policy produces `PolicyDecision` only. It does not execute, emit events, or
observe runtime behavior.

### INV-ARCH-2: Authoritative inputs remain the only policy inputs

`PolicyContext.inputs` remains the only policy input surface. No execution
traces, errors, timings, or observational fields enter policy evaluation.

### INV-ARCH-3: Determinism is enforced structurally

Given the same `PolicyContext` and the same root configuration, evaluation must
return the same `PolicyDecision`.

No:

- IO
- time
- randomness
- env lookup during evaluation
- mutable globals
- runtime caches that affect decisions

### INV-ARCH-4: Identity exists only at the root policy level

Inner gates are anonymous structures. Their identity is their canonical
description, not a policy ID.

### INV-ARCH-5: No hidden evaluator layer

There must be no engine, runtime interpreter, registry, or rule processor
between the composed gate structure and the resulting decision.

The composed structure is the governance function.

## Reason Model

The reason model should stay single-track.

- `reason_code` remains structural and machine-oriented
- optional `label` adds domain semantics without creating a second reason system

Example:

```text
reason_code: gate.bound.above:max_output_tokens
reason_message: {"actual":5000,"hi":4096,"key":"max_output_tokens","label":"output_token_limit"}
```

Rules:

- `reason_code` is always present and derived from gate structure.
- `label` is optional metadata on a gate.
- `label` may appear in `describe()` and in deterministic deny detail JSON.
- `label` must not alter the decision outcome.

This keeps reason aggregation simple while allowing domain meaning to travel
with the gate definition.

## Gateway Impact

The intended redesign should require minimal gateway change.

The gateway should continue to treat policy as an external decision surface.
The main required alignment is at the adapter boundary:

- prefer contract-level safe evaluation over adapter-local policy emulation
- stop narrowing authoritative inputs to scalar-only values when the contract
  allows JSON-safe structures
- keep gateway ownership limited to transport, enforcement, and event writing

This is a boundary correction, not a gateway architecture rewrite.

## Forbidden Moves

The following moves are out of bounds unless a future axiom-level need proves
them necessary:

- no YAML or declarative rule files
- no rule engine
- no policy evaluator runtime
- no second reason-code system
- no gateway-owned policy semantics
- no observation-derived governance
- no per-gate `policy_id` or `policy_version`

## Legacy Material

The pre-alignment `dbl_policy.policies` package is superseded and should not be
reintroduced.

Git history preserves it. The active package surface does not.

## Migration Plan

### Phase 1: `dbl-policy 0.3.0`

Refocus the package around protocol and contract.

- keep the current contract surface
- remove pre-alignment starter-pack code from the active package
- tighten README and docs around the contract role
- align the gateway adapter with contract-safe input handling

### Phase 2: `dbl-policy-gates 0.1.0`

Implement the algebra as a separate package.

- atomic gates
- combinators
- deterministic descriptions
- deterministic description digest
- structured reason detail JSON
- optional semantic `label`

### Phase 3: first domain policies

Build root-wrapped policies for actual governance use cases.

- root holds versioned identity
- inner tree holds deterministic structure
- release and drift reporting use `describe()` and `describe_digest()`

## Decision Summary

The architectural direction is:

- `dbl-policy` = protocol
- `dbl-policy-gates` = algebra
- domain policies = versioned root assemblies

This keeps the stack theory-aligned, minimizes gateway churn, and avoids
reintroducing a rule engine through the back door.
