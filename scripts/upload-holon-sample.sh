#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Eric Jahn
# Upload the holonic sample dataset in samples/holon/ to a pod container,
# filling in the pod's base URL. Safe to re-run: each file is PUT in place.
#
# Usage: scripts/upload-holon-sample.sh <pod> [container]
#   e.g. scripts/upload-holon-sample.sh billy          # -> /billy/holon/
#
# Environment:
#   JSS_URL       server base URL (default http://localhost:4443)
#   EMAIL, PASSWORD  pod owner's login; if unset, read from ACCOUNT_FILE
#   ACCOUNT_FILE  file with email=... and password=... lines
#                 (default ~/.config/jss-dev/<pod>-account.txt)
#
# Requires curl and jq.
set -euo pipefail

if [ $# -lt 1 ] || [ $# -gt 2 ] || [ -z "$1" ]; then
  sed -n '7,8p' "$0" >&2
  exit 2
fi

POD=$1
CONTAINER=${2:-holon}
CONTAINER=${CONTAINER%/}
JSS_URL=${JSS_URL:-http://localhost:4443}
JSS_URL=${JSS_URL%/}
ACCOUNT_FILE=${ACCOUNT_FILE:-$HOME/.config/jss-dev/$POD-account.txt}
SAMPLES=$(cd "$(dirname "$0")/../samples/holon" && pwd)

if [ -z "${EMAIL:-}" ] || [ -z "${PASSWORD:-}" ]; then
  [ -r "$ACCOUNT_FILE" ] || { echo "Set EMAIL and PASSWORD, or create $ACCOUNT_FILE" >&2; exit 1; }
  EMAIL=$(sed -n 's/^email=//p' "$ACCOUNT_FILE")
  PASSWORD=$(sed -n 's/^password=//p' "$ACCOUNT_FILE")
fi

POD_URL="$JSS_URL/$POD/"
BASE="$POD_URL$CONTAINER/"

TOKEN=$(jq -n --arg e "$EMAIL" --arg p "$PASSWORD" '{email: $e, password: $p}' \
  | curl -fsS -X POST "$JSS_URL/idp/credentials" -H 'Content-Type: application/json' --data-binary @- \
  | jq -r .access_token)
[ -n "$TOKEN" ] && [ "$TOKEN" != null ] || { echo "Login failed for $EMAIL" >&2; exit 1; }

# Templates use __POD__ for the pod root and __H__ for the target container.
for f in "$SAMPLES"/*.jsonld; do
  name=$(basename "$f")
  sed -e "s|__H__|$BASE|g" -e "s|__POD__|$POD_URL|g" "$f" \
    | curl -fsS -o /dev/null -w "PUT $BASE$name -> %{http_code}\n" \
      -X PUT "$BASE$name" -H "Authorization: Bearer $TOKEN" \
      -H 'Content-Type: application/ld+json' --data-binary @-
done

echo "Current state ($BASE""scene.jsonld):"
curl -fsS "${BASE}scene.jsonld" -H "Authorization: Bearer $TOKEN" -H 'Accept: application/ld+json' \
  | jq '.["@graph"][0]? // .'
