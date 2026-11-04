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

# The data and its boundary links use https://w3.org/ns/ucm# for terms and
# shapes alike. The shapes and lifecycle vocabulary still use
# urn:w3c:cg:ucm# and urn:w3c:cg:ucm:shapes#, so map both onto it.
def ucm_file(name):
    text = (open(os.path.join(UCM, name)).read()
            .replace("urn:w3c:cg:ucm:shapes#", "https://w3.org/ns/ucm#")
            .replace("urn:w3c:cg:ucm#", "https://w3.org/ns/ucm#"))
    return rdflib.Graph().parse(data=text, format="turtle")

ucm = ucm_file("unified-care-model.ttl") + ucm_file("ucm-lifecycle-vocabularies.ttl")
ucm_shapes = ucm_file("ucm-core-shapes.ttl")

failed = False
UCM_NS = "https://w3.org/ns/ucm#"
SH_NODE = rdflib.URIRef("http://www.w3.org/ns/shacl#NodeShape")
for shape in set(g["holon.jsonld"].objects(None, rdflib.URIRef("http://w3id.org/holon/boundary"))):
    if str(shape).startswith(UCM_NS) and (shape, rdflib.RDF.type, SH_NODE) not in ucm_shapes:
        print(f"boundary link {shape} is not a shape in ucm-core-shapes.ttl")
        failed = True
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
