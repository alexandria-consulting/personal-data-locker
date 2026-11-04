# Holonic sample data for a pod

A small, made-up dataset for the `billy` pod, shaped after Kurt Cagle's
holonic graph architecture: the W3C Holon Graph Community Group's
[HGA drafts](https://github.com/w3c-cg/holon/tree/main/architectures/hga)
and his posts in [The Inference Engineer](https://inferenceengineer.substack.com/)
("The Holonic Graph", "Fluents, Projections, and Observables",
"The Holon's Accountant", "A Holon Is a Recorder").

Upload with `make upload-holon-sample POD=billy` (goes to `/billy/holon/`).
`__POD__` and `__H__` in the files are replaced with the pod and container URLs.

| File | Holon layer | What's in it |
| --- | --- | --- |
| `holon.jsonld` | knowledge / registration | `holon:AgentHolon` Billy containing `holon:DataHolon` Billy's activity data; status, boundary, payload graph; fluent declarations |
| `events.jsonld` | event (history) graph, the payload | 7 append-only `hev:AssertionEvent` / `hev:ObservationEvent`s with bitemporal `hev:assertedAt` / `hev:receivedAt`, PROV-O activities and agents, supersession |
| `scene.jsonld` | scene / now graph | Current value of each fluent, materialised as plain triples on Billy, plus each fluent's head event |
| `boundary.jsonld` | boundary | SHACL shapes the events must satisfy |
| `projection.jsonld` | projection | `hproj:NowGraph` envelope pointing at the scene and event graphs |
| `vocab.jsonld` | (vocabulary) | Local `fl:` terms for fluents, events and observables |

What the data shows: Billy's full name is an observable derived from given and
family name; Billy's home city moved from Portland to Asheville (valid since
2026-08-15, recorded later); two resting heart rate readings from a phone
app, the second superseding the first.

Choices where the sources don't settle things:

- The HGA drafts have no fluent terms yet, so `fl:` (in `vocab.jsonld`)
  stands in for the pattern from "Fluents, Projections, and Observables".
  Supersession is written on the new event (`fl:supersedes`) so the history
  stays append-only.
- Each graph is its own Solid resource rather than a named graph in one
  dataset, so plain Solid clients can read each one.
- JSON-LD 1.1 can't express Turtle 1.2 triple reifiers, so the scene graph
  points each fluent at its head event instead of annotating each triple.
