#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Eric Jahn
"""Validate samples/holon/ before uploading.

Checks the events against the holon boundary (boundary.jsonld) and the UCM
payload (care.jsonld + scene.jsonld) against the UCM core shapes, with the
UCM vocabulary loaded into the data graph the way UCM's own test suite does.
Warnings count as failures.

Usage: scripts/check-holon-sample.py <path to a w3c-cg/ucm checkout>
Requires rdflib and pyshacl (pip install rdflib pyshacl).
"""
import os
import sys

import pyshacl
import rdflib

if len(sys.argv) != 2:
    sys.exit(__doc__)
UCM = sys.argv[1]
SAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "samples", "holon")
POD = "http://localhost:4443/billy/"
BASE = POD + "holon/"

g = {}
for f in sorted(x for x in os.listdir(SAMPLES) if x.endswith(".jsonld")):
    text = open(os.path.join(SAMPLES, f)).read().replace("__H__", BASE).replace("__POD__", POD)
    g[f] = rdflib.Graph().parse(data=text, format="json-ld", base=BASE + f)

# unified-care-model.ttl still uses https://w3.org/ns/ucm#; the shapes,
# lifecycle vocabulary and ucm-codegen use urn:w3c:cg:ucm#.
ucm = rdflib.Graph()
ucm.parse(data=open(os.path.join(UCM, "unified-care-model.ttl")).read()
          .replace("https://w3.org/ns/ucm#", "urn:w3c:cg:ucm#"), format="turtle")
ucm.parse(os.path.join(UCM, "ucm-lifecycle-vocabularies.ttl"), format="turtle")
ucm_shapes = rdflib.Graph().parse(os.path.join(UCM, "ucm-core-shapes.ttl"), format="turtle")

failed = False
for name, data, shapes, ont in [
    ("holon boundary", g["holon.jsonld"] + g["events.jsonld"], g["boundary.jsonld"], g["vocab.jsonld"]),
    ("UCM core shapes", g["care.jsonld"] + g["scene.jsonld"] + ucm, ucm_shapes, None),
]:
    ok, _, report = pyshacl.validate(data, shacl_graph=shapes, ont_graph=ont,
                                     inference="rdfs", advanced=True, allow_warnings=False)
    print(f"{name}: {'conforms' if ok else 'FAILS'}")
    if not ok:
        print(report)
        failed = True
sys.exit(1 if failed else 0)
