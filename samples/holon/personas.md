# Sample data personas

All people, organizations and readings here are fictional.

## Billy Testman

Billy is another client of the Eastside Neighbors team from UCM's
[nutrition story](https://github.com/w3c-cg/ucm/blob/main/user-stories/care-team-coordination-nutrition.md).
Billy's pod is their own copy of their care, and their UCM `Person` is their
WebID, `/billy/profile/card.jsonld#me`.

Billy's data has three holons, each declared in its own boundary graph:

- **Billy's personal data locker** (`holon:AgentHolon`, in
  `holon/boundary.jsonld`) is the parent. It holds Billy's food screening and
  where they live.
- **Billy's home monitoring** (`holon:DataHolon`, in
  `holon/home-monitoring/boundary.jsonld`) is a child holding the heart rate
  readings.
- **Billy's food security coordination** (`holon:ProcessHolon`, in
  `holon/food-security/boundary.jsonld`) is a child tracking the pantry
  handshake and whether Billy's food need is covered.

Each holon has its own scene, boundary, event and projection named graphs. See
the [README](README.md#holon-graph-names) for what those mean.

### What happens

In the **locker**:

1. Samuel Whitfield screens Billy for food insecurity (`SocialCareInteraction`
   with Billy in a `ClientRole`). The resulting `SocialCareStatement` says Billy
   runs out of food before the end of each month.
2. Billy records that they moved from Alder Street (since 2024) to Birch Court
   (since 2026-08-15), both entered on 2026-10-30.

In the **food security coordination**:

3. Samuel opens a `CareCoordinationInteraction` with the `ActivityFocus` food
   security, with Billy in a `BeneficiaryRole` and Samuel in a `CoordinatorRole`,
   and sends a `CoordinationRequest` to the pantry. Its `Handshake` is Pending,
   and Billy's food need is a `CareCoverageGap`.
4. Margit Halvorsen accepts for the pantry (`acceptsRequest`) in a `ProviderRole`,
   under a `PolicyDefinition` that limits the pantry to diet type and pickup
   details. The handshake is Accepted, and the gap becomes a `CareCommitment`.

In the **home monitoring**:

5. Billy's phone health app (a `Device`) sends two resting heart rate readings,
   64 and 61 bpm, as `ObservationStatement`s in Billy's `ClinicalCareContext`,
   with Billy in a `PatientRole`. The second supersedes the first as the latest
   reading.
