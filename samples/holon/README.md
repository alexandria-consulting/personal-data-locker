# Holonic sample data for a pod

A small, made-up dataset for the `billy` pod. Its structure follows Kurt
Cagle's holonic graph architecture: the W3C Holon Graph Community Group's
[HGA drafts](https://github.com/w3c-cg/holon/tree/main/architectures/hga)
and his posts in [The Inference Engineer](https://inferenceengineer.substack.com/).
Its content uses the [Unified Care Model](https://github.com/w3c-cg/ucm) and
fits the world of UCM's care-team user stories. [personas.md](personas.md)
describes who the data is about and what happens.

Upload with `make upload-holon-sample POD=billy` (goes to `/billy/holon/`).
`__POD__` and `__H__` in the files are replaced with the pod and container URLs.
Check it first with `scripts/check-holon-sample.py <path to a ucm checkout>`.

## Holon graph names

The sources name a holon's graphs differently. This dataset uses four named
graphs per holon: **scene**, **boundary**, **event** and **projection**. Every
other common name maps onto one of them:

| Graph here | Name in a source | Where it's used | Definition |
| --- | --- | --- | --- |
| **Scene** | Scene graph | ["The Holonic Graph"](https://inferenceengineer.substack.com/p/the-holonic-graph-a-new-architecture), ["The Holon's Accountant"](https://inferenceengineer.substack.com/p/the-holons-accountant) | What this is right now: current assertional state, with one current value per fluent |
| | Now graph | ["The Holonic Graph"](https://inferenceengineer.substack.com/p/the-holonic-graph-a-new-architecture), ["The Holon's Accountant"](https://inferenceengineer.substack.com/p/the-holons-accountant) | A view of current state derived from the history |
| **Boundary** | Boundary graph | [W3C Holon CG](https://www.w3.org/community/holon/) | The constraints and rules acting on the system, and the actions it exposes as interfaces |
| | Domain graph | ["The Holonic Graph"](https://inferenceengineer.substack.com/p/the-holonic-graph-a-new-architecture) | The rules and categories that govern the holon: SHACL shapes, OWL axioms, SKOS schemes |
| | Knowledge graph | ["The Holon's Accountant"](https://inferenceengineer.substack.com/p/the-holons-accountant), [W3C Holon CG](https://www.w3.org/community/holon/) | Declarations and identity, written once; the entities within the system |
| | Schema graph | ["The Holon's Accountant"](https://inferenceengineer.substack.com/p/the-holons-accountant) | What governs the knowledge graph's declarations |
| **Event** | Event graph | ["The Holon's Accountant"](https://inferenceengineer.substack.com/p/the-holons-accountant), [W3C Holon CG](https://www.w3.org/community/holon/) | The append-only log of how resources evolve over time |
| | Context graph | ["The Holonic Graph"](https://inferenceengineer.substack.com/p/the-holonic-graph-a-new-architecture), [W3C Holon CG](https://www.w3.org/community/holon/) | For whom, when and why something means what it means: author, time, authority, purpose, confidence |
| | History graph | ["The Holonic Graph"](https://inferenceengineer.substack.com/p/the-holonic-graph-a-new-architecture) | Append-only, never retracted: the ground truth of events |
| **Projection** | Projection | [W3C Holon CG](https://www.w3.org/community/holon/), [HGA `hproj:`](https://github.com/w3c-cg/holon/blob/main/architectures/hga/hga-pass-e-projection.databook.md) | A read-only map of the system, exposed outward |

Two names are not one of the four:

- **Holonic graph** ("The Holonic Graph") is the principle that the others
  compose, with every node a graph and every graph a node in a larger graph.
  It isn't a data graph.
- **Payload graph** (HGA `holon:payloadGraph`) is a pointer to the graph holding
  a holon's domain content. Here it points at the scene graph.

`hproj:NowGraph` is also different from the now graph above: it's the HGA class
for a read-only projection envelope, so it lives in the projection graph and
points at the scene graph through `hproj:sceneGraphBlock`.

## Layout

Each holon is a Solid container holding its four named graphs, and containers
nest the way the holons do:

```
holon/                     Billy's personal data locker
  scene.jsonld  boundary.jsonld  event.jsonld  projection.jsonld
  fluent-vocab.jsonld      shared fl: vocabulary, not part of any holon
  home-monitoring/         Billy's home monitoring
    scene.jsonld  boundary.jsonld  event.jsonld  projection.jsonld
  food-security/           Billy's food security coordination
    scene.jsonld  boundary.jsonld  event.jsonld  projection.jsonld
```

Each file is a JSON-LD named graph: its top-level `@id` is its own URL, and its
triples are in `@graph`.

| Graph | What's in it |
| --- | --- |
| `boundary.jsonld` | The holon's declaration, its fluents, and stable UCM things: people, locations, devices, contexts and policies. The parent's also holds the SHACL shapes for events and fluents, and its children reuse them by reference, along with the parent's shared entities |
| `event.jsonld` | Append-only `hev:` events with `hev:assertedAt` / `hev:receivedAt`, PROV-O provenance and fluent values, plus the UCM processes, participations and statements each event introduced |
| `scene.jsonld` | What's current: the UCM nodes still in force, each fluent's head event and value, and ordinary triples for fluents that stand for a property (`ucm:locatedAt`, `ucm:hasLifecycleState`) |
| `projection.jsonld` | An `hproj:NowGraph` envelope pointing at the holon's scene and event graphs |

## The fluent vocabulary

`fluent-vocab.jsonld` defines the `fl:` terms the holons use to record values
that change over time. Cagle's "Fluents, Projections, and Observables" and "A
Holon Is a Recorder" describe this pattern, but the W3C Holon CG's HGA drafts
don't define terms for it yet, so this file is a local stand-in. Replace `fl:`
with the CG's terms once they're published.

It's a shared definition rather than data about Billy, so it sits beside the
holons, outside all four of their graphs. It's the only `.jsonld` file here that
isn't a named graph. Its terms' IRIs are under the file's own URL, so on this
server `fl:Fluent` is
`http://localhost:4443/billy/holon/fluent-vocab.jsonld#Fluent`.

| Term | Used in | Meaning |
| --- | --- | --- |
| `fl:Fluent` | boundary | A stable node standing for the current value of something that varies, backed by an append-only stream of events |
| `fl:Observable` | boundary | A fluent derived from other fluents and recomputed when any of them changes |
| `fl:hasFluent` | boundary | Links a holon to a fluent it tracks |
| `fl:subject` | boundary | The resource the fluent describes |
| `fl:property` | boundary | The property the fluent stands for, if any; the scene graph then states it as an ordinary triple |
| `fl:observes` | boundary | A fluent an observable is computed from |
| `fl:fluent` | event | The fluent an event records a value for |
| `fl:value` | event | The value the event records |
| `fl:supersedes` | event | The earlier event on the same fluent that this event replaces, written on the new event so the history stays append-only |
| `fl:headEvent` | scene | The event currently holding the fluent: the latest one nothing supersedes |
| `fl:currentValue` | scene | The fluent's value as of its head event |

## Viewing what's in the pod

Use `curl` with Billy's login token. This server has no pod browser: opening
<http://localhost:4443/billy/> shows raw JSON-LD, and `/billy/holon/` answers
401 because a browser tab isn't logged in:

```json
{"error":"Unauthorized","message":"Authentication required"}
```

Run these in the same terminal, with the server up. First, get a token, which
you should treat like a password:

```bash
F=~/.config/jss-dev/billy-account.txt; TOKEN=$(jq -n --arg e "$(sed -n 's/^email=//p' $F)" --arg p "$(sed -n 's/^password=//p' $F)" '{email: $e, password: $p}' | curl -s -X POST http://localhost:4443/idp/credentials -H 'Content-Type: application/json' --data-binary @- | jq -r .access_token)
```

List what's in a container:

```bash
curl -s http://localhost:4443/billy/holon/ -H "Authorization: Bearer $TOKEN" | jq -r '.contains[]? // .["ldp:contains"][]? | .["@id"]? // .'
```

```text
http://localhost:4443/billy/holon/boundary.jsonld
http://localhost:4443/billy/holon/event.jsonld
http://localhost:4443/billy/holon/fluent-vocab.jsonld
http://localhost:4443/billy/holon/food-security/
http://localhost:4443/billy/holon/home-monitoring/
http://localhost:4443/billy/holon/projection.jsonld
http://localhost:4443/billy/holon/scene.jsonld
```

The same command works on any container. Use `/billy/` for the pod root, or add
`home-monitoring/` or `food-security/` to the holon path.

Read a file:

```bash
curl -s http://localhost:4443/billy/holon/food-security/scene.jsonld -H "Authorization: Bearer $TOKEN" -H 'Accept: application/ld+json' | jq '.["@graph"]'
```

This prints the whole graph. The end of it shows that the pantry handshake is
currently Accepted, and which event set that state:

```json
  {
    "@id": "http://localhost:4443/billy/holon/food-security/event.jsonld#pantry-handshake",
    "ucm:hasLifecycleState": {
      "@id": "ucm:Accepted"
    }
  },
  {
    "@id": "http://localhost:4443/billy/holon/food-security/boundary.jsonld#pantry-handshake-state",
    "fl:headEvent": {
      "@id": "http://localhost:4443/billy/holon/food-security/event.jsonld#e3"
    },
    "fl:currentValue": {
      "@id": "ucm:Accepted"
    }
  }
```

Keep the `Accept: application/ld+json` header. JSS's `text/turtle` conversion of
these files is lossy: it leaves compact IRIs unexpanded (`<ucm:Accepted>`), drops
nested nodes with no `@id` (so the SHACL shapes come back empty), and loses the
graph name.

## How the two models meet

- **UCM is the content; the holon is the envelope.** Each event's
  `hev:assertionPayload`, `hev:observationPayload` or `hev:commandPayload`
  points at the UCM nodes it introduced.
- **Fluents give UCM temporalized state.** UCM's shapes allow a process one
  `hasLifecycleState` and note that this should relax "once temporalized
  state assertions exist". Here the handshake's Pending and Accepted live as
  events in the history, and only the current state is in the scene graph.
  The same goes for where Billy lives (`ucm:locatedAt`).
- **Coverage is an observable.** "Is Billy's food need covered?" observes the
  handshake state and moves from `CareCoverageGap` to `CareCommitment`.

Validation: the checker confirms each holon is exactly these four named graphs,
the events conform to the shapes in the boundary graphs, and the boundary, event
and scene graphs together produce zero results, warnings included, against
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
- A statement still in force appears in both the event and scene graphs, as
  identical triples, so the history stays self-contained when the scene changes.
- JSON-LD 1.1 can't express Turtle 1.2 triple reifiers, so the scene graph
  points each fluent at its head event instead of annotating each triple.
