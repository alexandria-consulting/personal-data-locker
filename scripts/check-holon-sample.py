#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Eric Jahn
"""Validate samples/holon/ before uploading.

Checks that each holon is exactly four named graphs (scene, boundary, event,
projection), each named after its own file; that events conform to the holon
boundary shapes; and that the UCM content conforms to UCM's core shapes, with
the UCM vocabulary loaded into the data graph the way UCM's own test suite
does. Warnings count as failures.

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
GRAPHS = ["scene", "boundary", "event", "projection"]
HOLONS = ["", "home-monitoring/", "food-security/"]
UCM_NS = "https://www.w3.org/ns/ucm#"

failed = False


def fail(message):
    global failed
    print(message)
    failed = True


def load(rel):
    text = open(os.path.join(SAMPLES, rel)).read().replace("__H__", BASE).replace("__POD__", POD)
    ds = rdflib.Dataset()
    ds.parse(data=text, format="json-ld", base=BASE + rel)
    return ds


named = {}
for holon in HOLONS:
    for name in GRAPHS:
        rel = f"{holon}{name}.jsonld"
        ds = load(rel)
        iri = rdflib.URIRef(BASE + rel)
        names = {g.identifier for g in ds.graphs() if len(g) and g.identifier != ds.default_graph.identifier}
        if names != {iri} or len(ds.default_graph):
            fail(f"{rel}: expected one named graph <{iri}> and an empty default graph, got {names}")
        named[rel] = ds.graph(iri)
print(f"named graphs: {len(named)} across {len(HOLONS)} holons")


def union(*suffixes):
    g = rdflib.Graph()
    for rel, graph in named.items():
        if os.path.basename(rel) in suffixes:
            g += graph
    return g


ucm = rdflib.Graph().parse(os.path.join(UCM, "unified-care-model.ttl"), format="turtle")
ucm_shapes = rdflib.Graph().parse(os.path.join(UCM, "ucm-core-shapes.ttl"), format="turtle")
vocab = load("fluent-vocab.jsonld")
vocab_graph = rdflib.Graph()
for s, p, o, _ in vocab.quads():
    vocab_graph.add((s, p, o))

boundary = union("boundary.jsonld")
SH_NODE = rdflib.URIRef("http://www.w3.org/ns/shacl#NodeShape")
for shape in set(boundary.objects(None, rdflib.URIRef("http://w3id.org/holon/boundary"))):
    if str(shape).startswith(UCM_NS):
        if (shape, rdflib.RDF.type, SH_NODE) not in ucm_shapes:
            fail(f"boundary link {shape} is not a shape in ucm-core-shapes.ttl")
    elif (shape, rdflib.RDF.type, SH_NODE) not in boundary:
        fail(f"boundary link {shape} is not a shape in a boundary graph")

for name, data, shapes, ont in [
    ("holon boundary", boundary + union("event.jsonld"), boundary, vocab_graph),
    # Each holon's event and scene graphs both describe current UCM nodes,
    # with identical triples, so the union holds no conflicting values.
    ("UCM core shapes", boundary + union("event.jsonld", "scene.jsonld") + ucm, ucm_shapes, None),
]:
    ok, _, report = pyshacl.validate(data, shacl_graph=shapes, ont_graph=ont,
                                     inference="rdfs", advanced=True, allow_warnings=False)
    print(f"{name}: {'conforms' if ok else 'FAILS'}")
    if not ok:
        print(report)
        failed = True
sys.exit(1 if failed else 0)
