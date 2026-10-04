# Test-Gated Coding Agent Prompt

This template is intended for multi-component coding tasks handled by AI coding agents. It separates global design context from local implementation scope.

The agent receives the complete architecture upfront, but implementation proceeds through independently testable components with explicit gates.

This pattern is intended to reduce unnecessary context expansion, cross-component rework, and debugging while preserving global architectural awareness.

Replace the bracketed placeholders before use. Define executable gate commands and pass criteria for each component. Copy the component pattern for additional components. A checkpoint is a recorded passing state; do not commit or push unless instructed. Begin with the implementation plan, then Component 1. Progress between components follows the selected Execution Mode.

## Execution Mode

Choose one before starting:

- **Interactive:** Stop after every passing component gate and wait for explicit approval before proceeding.
- **Autonomous:** After a component gate passes, record the checkpoint and automatically proceed to the next predefined component. After the last component gate passes, proceed to the final integration gate. Stop only if a gate fails, the specification is ambiguous, or implementation would require expanding the approved scope.

Selected mode: [Interactive or Autonomous]

If no mode is selected, ask which mode to use before implementation begins.

## 1. Project Goal

[Describe the overall feature/system being built.]

Understand the complete goal and architecture before implementation begins.

## 2. Architecture / Components

[List all relevant components and their relationships.]

Example:

```text
Component A
    ↓
Component B
    ↓
Component C
```

[Explain interfaces, input/output contracts, and dependencies between components. Identify how each component can be tested independently.]

## 3. Global Constraints

[List constraints that apply to the entire implementation. Adapt these examples to the project:]

- Do not modify unrelated files.
- Preserve existing public interfaces unless explicitly allowed.
- Reuse existing infrastructure where possible.
- Do not rebuild existing data/resources unnecessarily.
- Maintain backward compatibility.
- Follow existing repository conventions.

## 4. Acceptance Criteria

[List the final system-level requirements and measurable pass criteria.]

[Specify the final acceptance/integration suite and commands.]

These define what “done” means for the complete task.

## 5. Implementation Plan

Before writing code:

1. Inspect the relevant repository structure.
2. Identify the minimum files needed.
3. Identify component boundaries.
4. Identify dependencies between components.
5. Propose an ordered implementation plan.

Do not implement the entire system yet. After presenting the plan, implement only Component 1 within the boundary below. Surface any blocking ambiguity before dependent work.

## 6. Component 1 — [Name]

Implement ONLY:

[Component/files, including permitted component tests.]

Requirements:

[Component-specific requirements.]

Do not implement:

[Future components.]

Gate:

[Test commands and explicit pass criteria.]

After implementation:

1. Run relevant unit/component tests.
2. Fix failures attributable to this component and rerun affected tests.
3. Report files changed, tests run, test results, assumptions, and remaining issues.
4. Record the passing checkpoint and its test evidence.

After the gate passes, follow the selected Execution Mode:

- **Interactive:** Stop and wait for approval.
- **Autonomous:** Record the passing checkpoint and proceed to the next predefined component, or the final integration gate if all components are complete.

In either mode, stop and report the blocker if the gate fails or cannot run, the specification is ambiguous, or proceeding requires expanding the approved scope. Do not bypass the gate.

## 7. Component 2 — [Name]

Begin only after Component 1 has passed its gate and the selected Execution Mode permits proceeding.

Implement ONLY:

[Component/files, including permitted component tests.]

Requirements:

[Component-specific requirements.]

Treat Component 1’s tested interface as stable. Do not rewrite Component 1 unless an integration/interface defect requires it. If a change is required, explain the demonstrated defect and why the change is necessary before making it.

Gate:

[Component 2 test commands, relevant Component 1 regression commands, and explicit pass criteria.]

After implementation:

1. Run Component 2 tests.
2. Run relevant Component 1 regression tests.
3. Fix failures attributable to this component or demonstrated integration defects, then rerun affected tests.
4. Report files changed, tests run, test results, assumptions, and remaining issues.
5. Record the passing checkpoint and its test evidence.

After the gate passes, follow the selected Execution Mode:

- **Interactive:** Stop and wait for approval.
- **Autonomous:** Record the passing checkpoint and proceed to the next predefined component, or the final integration gate if all components are complete.

In either mode, stop and report the blocker if the gate fails or cannot run, the specification is ambiguous, or proceeding requires expanding the approved scope. Do not bypass the gate.

## 8. Additional Components

[Add a section for each additional component with its boundary, requirements, excluded future work, test commands, pass criteria, and reporting requirements. Write “not applicable” if there are none.]

Repeat the same pattern:

```text
Implement → test → fix → checkpoint → next component
```

Follow the selected Execution Mode at every component gate. Keep previously tested interfaces stable and run relevant regression tests. Stop if a gate fails or cannot run, the specification is ambiguous, or proceeding requires expanding the approved scope.

## 9. Final Integration Gate

Begin only after all component gates pass. In Interactive mode, wait for approval to run final integration; in Autonomous mode, proceed automatically:

1. Run the full acceptance/integration suite defined in Section 4.
2. Do not proactively rewrite working components.
3. Fix only demonstrated integration defects.
4. Run affected regression tests after fixes and rerun the final suite.

Report:

- Final files changed.
- Tests passed/failed, including commands and any skipped or unexecuted tests.
- Integration fixes and the evidence requiring them.
- Known limitations.
- Deviations from the original specification.

If the final gate fails or cannot run, report the failure/blocker; do not claim the task is complete.

## 10. Coding-Agent Rules

- Understand globally; implement locally.
- Keep the full architecture in mind.
- Work on only the current implementation boundary.
- Do not reread or reanalyze unrelated parts of the repository unless new evidence shows they are required for the current component.
- Do not implement future components early.
- Do not refactor already-passing components without evidence that a change is required.
- Prefer existing interfaces and abstractions.
- Run the smallest relevant test suite first.
- Use broader regression tests at component boundaries.
- Preserve passing checkpoints.
- Surface ambiguity instead of silently expanding scope.
- Do not claim tests passed unless they were actually executed.
- Follow the selected Execution Mode after each passing component gate.
- In either mode, stop if a gate fails or cannot run, the specification is ambiguous, or proceeding requires expanding the approved scope.
