# 06 Implementation Work Packages Standard

This standard explains how implementation should be split. Exact package IDs and handoff payloads live in:

```text
interface-specs/05-handoff-package-interface.md
```

## Principle

Do not give one model the entire system as one task. Split implementation into bounded work packages with explicit allowed paths, forbidden paths, acceptance commands, and handoff notes.

## Recommended Package Groups

```text
Schema lock
Queue and lease system
Agent task packet system
DB indexer
CLI
WebUI state/API
Proof validator
Docs/Evidence store
Committer
Freeze
Compiler dry run
Audit
Integration demo
```

## Parallel Development

Packages can run in parallel only when they do not write the same files or change shared schemas without coordination.

Good parallel split:

```text
DB indexer
WebUI state reader
Proof validator
Docs store
```

Bad parallel split:

```text
two packages redefining ProofResult
two packages changing queue status enums
two packages writing graph mutation logic
```

## Package Acceptance

Every implementation package needs:

```text
focused tests
clear changed paths
known limits
package_status record
handoff notes for dependent packages
```

Integration should happen only after schema and interface contracts are stable.
