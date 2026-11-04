# Holonic sample data for a pod

A small, made-up dataset for the `billy` pod. Its structure follows Kurt
Cagle's holonic graph architecture: the W3C Holon Graph Community Group's
[HGA drafts](https://github.com/w3c-cg/holon/tree/main/architectures/hga)
and his posts in [The Inference Engineer](https://inferenceengineer.substack.com/)
("The Holonic Graph", "Fluents, Projections, and Observables",
"The Holon's Accountant", "A Holon Is a Recorder"). Its content uses the
[Unified Care Model](https://github.com/w3c-cg/ucm) and fits the world of
UCM's care-team user stories.

Upload with `make upload-holon-sample POD=billy` (goes to `/billy/holon/`).
`__POD__` and `__H__` in the files are replaced with the pod and container URLs.
Check it first with `scripts/check-holon-sample.py <path to a ucm checkout>`.

## The story

Billy Testman is another client of the Eastside Neighbors team from UCM's
[nutrition story](https://github.com/w3c-cg/ucm/blob/main/user-stories/care-team-coordination-nutrition.md).
His pod is his own copy of his care.

1. Samuel Whitfield screens Billy for food insecurity (`SocialCareInteraction`
   with Billy in a `ClientRole`). His `SocialCareStatement`: Billy runs out of
   food before the end of each month.
2. Samuel opens a `CareCoordinationInteraction` with the `ActivityFocus` food
   security, with Billy in a `BeneficiaryRole` and himself in a
   `CoordinatorRole`. He sends a `CoordinationRequest` to the pantry; its
   `Handshake` is Pending. Billy's food need is now a `CareCoverageGap`.
3. Margit Halvorsen accepts for the pantry (`acceptsRequest`) in a
   `ProviderRole`, under a `PolicyDefinition` that limits the pantry to diet
   type and pickup details. The handshake is Accepted and the gap becomes a
   `CareCommitment`.
4. Billy records that he moved from Alder Street (since 2024) to Birch Court
   (since 2026-08-15), both entered on 2026-10-30.
5. His phone sends two resting heart rate readings as `ObservationStatement`s
   in his `ClinicalCareContext`, with Billy in a `PatientRole`.

Billy's UCM `Person` is his WebID, so his identity stays the one his pod
already has.

## Files

| File | Holon layer | What's in it |
| --- | --- | --- |
| `holon.jsonld` | registration / knowledge | Billy's locker (`holon:AgentHolon`) containing his home monitoring (`holon:DataHolon`) and his food security coordination (`holon:ProcessHolon`); fluent declarations |
| `care.jsonld` | payload graph | UCM entities, contexts, processes, participations and statements. Nothing in it changes; changing values live in fluents |
| `events.jsonld` | event (history) graph | 9 append-only `hev:` events with `hev:assertedAt` / `hev:receivedAt`, PROV-O provenance, payload pointers into `care.jsonld`, and fluent values with supersession |
| `scene.jsonld` | scene / now graph | Current value of each fluent, materialised as UCM triples (`ucm:locatedAt`, `ucm:hasLifecycleState`) |
| `boundary.jsonld` | boundary | SHACL shapes for events. The holons also name UCM's own core shapes (`ucm:ParticipationShape`, `ucm:StatementShape`) as their boundary |
| `projection.jsonld` | projection | `hproj:NowGraph` envelope pointing at the scene and event graphs |
| `vocab.jsonld` | (vocabulary) | Local `fl:` terms for fluents, events and observables |

## How the two models meet

- **UCM is the payload; the holon is the envelope.** Each event's
  `hev:assertionPayload`, `hev:observationPayload` or `hev:commandPayload`
  points at the UCM nodes it introduced.
- **Fluents give UCM temporalized state.** UCM's shapes allow a process one
  `hasLifecycleState` and note that this should relax "once temporalized
  state assertions exist". Here the handshake's Pending and Accepted live as
  events in the history, and only the current state is in the scene graph.
  The same goes for where Billy lives (`ucm:locatedAt`).
- **Coverage is an observable.** "Is Billy's food need covered?" observes the
  handshake state and moves from `CareCoverageGap` to `CareCommitment`.

Validation: the events conform to `boundary.jsonld`, and `care.jsonld` plus
`scene.jsonld` produce zero results, warnings included, against
`ucm-core-shapes.ttl`.

## Choices where the sources don't settle things

- The HGA drafts have no fluent terms yet, so `fl:` stands in for the pattern
  from "Fluents, Projections, and Observables".
- Everything UCM uses the `https://w3.org/ns/ucm#` namespace, including the
  holons' boundary links to UCM's shapes (`ucm:ParticipationShape`,
  `ucm:StatementShape`). The published core shapes and lifecycle vocabulary
  still use `urn:w3c:cg:ucm#` and `urn:w3c:cg:ucm:shapes#`, so
  `check-holon-sample.py` maps both onto `https://w3.org/ns/ucm#` before
  validating, and checks that each linked shape exists.
- UCM has no property for a reading's value, so each observation uses
  `rdf:value` and a LOINC code in `dcterms:type`.
- Each graph is its own Solid resource rather than a named graph in one
  dataset, so plain Solid clients can read each one.
- JSON-LD 1.1 can't express Turtle 1.2 triple reifiers, so the scene graph
  points each fluent at its head event instead of annotating each triple.
