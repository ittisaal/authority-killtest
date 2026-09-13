# State-transition model

This note fixes the paper's core semantics without claiming new generic reachability theory.

## State

Let a system state be

\[
s = (V, A, G, P)
\]

where:

- `V` is the current valuation of policy-bearing variables (repository properties, workflow/configuration choices, identity-claim inputs, etc.);
- `A` is the authority relation describing which principals may perform which mutations in the current state;
- `G` is the set of fixed or independently controlled guards visible to the analysis; and
- `P` is the downstream policy/configuration used to compute effective capabilities.

Each variable `x` has an allowed domain `D(x)`. The domain is part of the semantics: a writer cannot reach a value outside `D(x)`.

## Authorized transition

For actor `a`, a mutation transition

\[
s \xrightarrow{a:m} s'
\]

exists only if mutation `m` is authorized by `A` in state `s` and produces a value allowed by the relevant domain. After the mutation, dynamic authority/capabilities are recomputed. Therefore authority may evolve along a path rather than remaining fixed at the initial state.

Let `Reach(a,s)` be the least set containing `s` and closed under actor-authorized transitions.

## Effective privilege / protection state

For workload or protected action `w`, let

\[
Priv(w,s)
\]

be the effective capability set after evaluating the composed policies in state `s`.

The set may include ordinary permissions such as an external read capability, and normalized protection capabilities such as:

- direct update of a protected branch;
- merge without a required approval;
- required check reports success without evaluating the protected artifact;
- protected analysis does not execute.

Representing protection loss as an effective capability keeps the decision rule uniform.

## Unsafe reachability

The primary property is:

\[
Unsafe(a,w,s) \iff \exists s' \in Reach(a,s): Priv(w,s') \setminus Priv(w,s) \neq \varnothing.
\]

The reported delta is

\[
\Delta(a,w,s,s') = Priv(w,s') \setminus Priv(w,s).
\]

This is a **marginal** test. If the actor/workload already has the destination capability in the initial state, reaching it through another metadata path is not a new privilege under this property.

## Safe counterexamples

A mutable variable is not sufficient for `Unsafe`.

Typical reasons a path is safe include:

1. the actor lacks write authority for the required variable;
2. the allowed domain contains no value that reaches the relevant policy state;
3. an independent fixed guard remains false/unsatisfied for every actor-reachable state;
4. the apparent producer and consumer merely coexist but are not connected;
5. the destination capability already exists initially, so the marginal delta is empty.

These distinctions correspond directly to the controlled S2/S3 cases and the frozen public safe cases.

## Unknown / incomplete

Let `Obs` be the policy facts available to the analyzer. `unknown` is returned when `Obs` is insufficient to establish either unsafe reachability or the conditions needed to rule it out. Examples include:

- consumer behavior is visible but property editability/provenance is not;
- editability is visible but the downstream consumer is not;
- a federation edge is visible but the downstream trust condition/permission is unavailable.

Unknown is not coerced to safe or unsafe.

## Witness

For an unsafe result, return a shortest mutation witness

\[
\pi = (m_1, m_2, \ldots, m_k)
\]

such that applying `pi` from `s` reaches a state with non-empty `Delta`. The prototype uses breadth-first search over finite actor-authorized mutations, recomputing dynamic capabilities after each transition.

The witness must report:

- actor;
- mutations and changed values;
- producer/consumer policy edges used;
- final effective capability delta.

## Repair cut

Let `Paths(s,a,w)` be the set of unsafe witness paths under the analysis model. A repair set `R` is sufficient when every unsafe path intersects at least one edge or condition removed/strengthened by `R`:

\[
\forall \pi \in Paths(s,a,w),\; \pi \cap R \neq \varnothing.
\]

The minimum-edge repair is a hitting-set problem, but minimum edge count need not be the preferred operational repair. Each candidate may therefore carry a cost vector such as automation disruption, administrative scope, repositories affected, and downstream systems touched. The implementation reports both minimum-cardinality cuts and the non-dominated (Pareto) cost frontier.

## Claim boundary

The contribution is not a new theorem about graph reachability or ABAC. The research contribution is the extraction and composition of authority provenance, policy-bearing metadata, CI/CD policy selection and identity claims, downstream authorization/protection semantics, witnesses, and repairs into this decision problem.
