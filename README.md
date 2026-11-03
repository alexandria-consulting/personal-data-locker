# Personal data locker (JSS on Podman)

A contained development install of the [JavaScript Solid Server](https://jss.live/)
(npm `javascript-solid-server`). Everything runs inside a Podman pod; nothing is
installed on the host except Podman (and, optionally, Caddy for HTTPS).

## Layout

| Path | Purpose |
| --- | --- |
| `jss/Containerfile` | Image: Node 22 + `javascript-solid-server` (pinned via `JSS_VERSION`) |
| `jss.yaml` | Kubernetes v1 Pod run with `podman kube play` (volumes `jss-data`, `jss-secrets`) |
| `profiles/local.yaml` | ConfigMap for `http://localhost:4443/` |
| `profiles/lan.yaml` | ConfigMap for LAN access (`0.0.0.0:4443`) |
| `profiles/internet.yaml` | ConfigMap for a public HTTPS domain behind Caddy, invite-only |
| `profiles/*.local.yaml` | Your machine-specific copies of the profiles (gitignored, used automatically) |
| `proxy/Caddyfile` | Host-side Caddy reverse proxy (internet site, LAN `tls internal` example) |
| `scripts/grant-webid.sh` | Grant a WebID access to a container, keeping existing ACL rules |
| `Makefile` | Build / run / inspect / reset commands |

## Install (Ubuntu)

```bash
sudo apt install -y podman make
```

## Commands

| Command | What it does |
| --- | --- |
| `make up` | Build the image and start the pod (`PROFILE=local` by default) |
| `make up PROFILE=lan` | Same, with the `lan` profile, published on `0.0.0.0:4443` |
| `make up PROFILE=internet` | Same, with the `internet` profile, on `127.0.0.1:4443` behind Caddy |
| `make down` | Stop and remove the pod (volumes are kept) |
| `make restart` | `down` then `up` |
| `make logs` | Follow server logs |
| `make status` | Show pod, container, and volume state |
| `make shell` | Shell inside the server container (e.g. for `jss invite create`) |
| `make rebuild` | Rebuild the image without cache, then restart |
| `make reset` | Stop the pod and, after confirmation, delete all data and secrets |
| `make caddy-validate` | Check `proxy/Caddyfile` in a throwaway Caddy container |
| `make grant-webid POD=… CONTAINER=… WEBID=…` | Give a WebID Read/Write/Control on a container |

Pass the same `PROFILE=` to `restart` and `rebuild` that you used for `up`.

## Create a pod (account)

With the server up on the local profile:

```bash
curl -X POST http://localhost:4443/.pods \
  -H 'Content-Type: application/json' \
  -d '{"name":"eric","email":"eric@example.com","password":"choose-a-password"}'
```

The WebID is `http://localhost:4443/eric/profile/card.jsonld#me` and the pod
root is `http://localhost:4443/eric/`. The response also contains a
long-lived `token` for the new account; treat it like a password.

The test account's login is saved in `~/.config/jss-dev/test-account.txt`
(outside the repo, mode 600). Its WebID is
`http://localhost:4443/test/profile/card.jsonld#me`.

## Get a token and write a resource

```bash
TOKEN=$(curl -s -X POST http://localhost:4443/idp/credentials \
  -H 'Content-Type: application/json' \
  -d '{"email":"eric@example.com","password":"choose-a-password"}' | jq -r .access_token)
```

```bash
curl -X PUT http://localhost:4443/eric/notes/hello.txt \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: text/plain' \
  --data 'Hello, Solid'
```

## Profiles

Each profile is a ConfigMap named `jss-config` passed to `podman kube play
--configmap`; its variables become the container's environment. If
`profiles/<profile>.local.yaml` exists, `make` uses it instead of the committed
file. Put your real hostname, IP, or domain there, not in the committed file:

```bash
cp profiles/internet.yaml profiles/internet.local.yaml
```

`JSS_IDP_ISSUER` must exactly match the URL clients use to reach the server
(scheme, host, port, trailing slash). If it doesn't, tokens are issued for the
wrong issuer and logins fail. Run `make restart PROFILE=…` after changing it.

| Profile | Issuer | Bound to | Notes |
| --- | --- | --- | --- |
| `local` | `http://localhost:4443/` | `127.0.0.1:4443` | Default; this machine only |
| `lan` | `http://CHANGE-ME.local:4443/` | `0.0.0.0:4443` | Plain HTTP on the LAN; see below |
| `internet` | `https://CHANGE-ME.example.com/` | `127.0.0.1:4443` | Behind Caddy; `JSS_INVITE_ONLY=true`, log level `warn` |

**LAN.** Set the issuer to this machine's LAN address in
`profiles/lan.local.yaml` (e.g. `http://192.168.1.146:4443/`), then
`make up PROFILE=lan` and check from another device:

```bash
curl -i http://192.168.1.146:4443/test/public/
```

This opens port 4443 to your whole network, so use it only on networks you
trust. Browsers only allow Solid-OIDC login over HTTPS or on `localhost`, so
plain-HTTP LAN access is fine for reads and for scripts using Bearer tokens,
but not for browser logins. For those, keep JSS on the `local` binding, run
Caddy with `tls internal` (below), and set the issuer to Caddy's `https://` URL.

## HTTPS with Caddy

Caddy runs on the host because rootless Podman can't bind ports below 1024 by
default. `proxy/Caddyfile` forwards everything to `127.0.0.1:4443`. Caddy
passes the original `Host` and sets `X-Forwarded-*`, which JSS honors
(`trustProxy`), and it proxies WebSocket notifications with no extra config.
It also blocks `/storage/*` (see [Security](#security-notes-for-going-public)).

1. Point DNS for your domain (an A and/or AAAA record) at this host, and make
   sure ports 80 and 443 reach it from the internet (router port forwarding,
   firewall). Let's Encrypt needs both to issue the certificate.
2. Install Caddy:

   ```bash
   sudo apt install -y caddy
   ```

3. Replace `CHANGE-ME.example.com` in `proxy/Caddyfile` with your domain, check
   it, and install it:

   ```bash
   make caddy-validate
   ```

   ```bash
   sudo cp proxy/Caddyfile /etc/caddy/Caddyfile && sudo systemctl reload caddy
   ```

4. Set the same domain in `profiles/internet.local.yaml` and start JSS:

   ```bash
   make up PROFILE=internet
   ```

5. Create accounts with invite codes:

   ```bash
   podman exec -it jss-server jss invite create --help
   ```

For HTTPS on the LAN, uncomment the `CHANGE-ME.local` block (`tls internal`),
run `sudo caddy trust`, and install Caddy's root certificate on the other
devices.

## Granting access to an external WebID

`scripts/grant-webid.sh` logs in as the pod owner, reads the container's
`.acl`, keeps every existing authorization, adds (or replaces) one for the
given WebID with `acl:accessTo` and `acl:default` on `./`, writes it back, and
prints the result:

```bash
make grant-webid POD=test CONTAINER=private WEBID='https://alexandriaconsulting.com/files/eric_jahn.rdf#me'
```

By default it reads the owner's login from `~/.config/jss-dev/<pod>-account.txt`
(`email=` and `password=` lines); set `EMAIL` and `PASSWORD`, `ACCOUNT_FILE`,
`JSS_URL`, or `MODES="Read Write"` in the environment to change that. Re-running
it is safe.

To do it by hand, note that JSS only accepts ACLs as JSON-LD
(`application/ld+json` or `application/json`; Turtle gets a 415). Keep the
owner rule so you don't lock yourself out:

```bash
curl -X PUT http://localhost:4443/eric/shared/.acl \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/ld+json' \
  --data-binary @- <<'EOF'
{
  "@context": { "acl": "http://www.w3.org/ns/auth/acl#" },
  "@graph": [
    {
      "@id": "#owner",
      "@type": "acl:Authorization",
      "acl:agent": { "@id": "../profile/card.jsonld#me" },
      "acl:accessTo": { "@id": "./" },
      "acl:default": { "@id": "./" },
      "acl:mode": [{ "@id": "acl:Read" }, { "@id": "acl:Write" }, { "@id": "acl:Control" }]
    },
    {
      "@id": "#eric-external",
      "@type": "acl:Authorization",
      "acl:agent": { "@id": "https://alexandriaconsulting.com/files/eric_jahn.rdf#me" },
      "acl:accessTo": { "@id": "./" },
      "acl:default": { "@id": "./" },
      "acl:mode": [{ "@id": "acl:Read" }, { "@id": "acl:Write" }, { "@id": "acl:Control" }]
    }
  ]
}
EOF
```

**Logging in as an external WebID.** A Solid app can only use that WebID if
its profile document names an identity provider (`solid:oidcIssuer`) that
issues tokens for it, and the document is served with an RDF content type
(`text/turtle`, `application/rdf+xml`, or `application/ld+json`) and CORS
headers (`Access-Control-Allow-Origin: *`) so browser apps can read it. As of
2026-11-02, `https://alexandriaconsulting.com/files/eric_jahn.rdf` declares
`solid:oidcIssuer https://solidcommunity.net`, but it's served as
`application/octet-stream` with no CORS header. Fix the web server's
content type for `.rdf` (e.g. Apache `AddType application/rdf+xml .rdf`) and
add the CORS header. The login then happens at solidcommunity.net, not at this
JSS.

## Security notes for going public

- **Keep JSS on 127.0.0.1 behind Caddy.** Use the `internet` profile (bound to
  `127.0.0.1:4443`) and never forward port 4443 on your router. Only 80/443
  (Caddy) should be reachable.
- **remoteStorage bypasses WAC.** JSS 0.0.224 always enables a remoteStorage
  endpoint at `/storage/me/...` that maps onto the whole data directory and lets
  *any* logged-in account read and write *every* pod's files, ignoring ACLs.
  There's no setting to turn it off. `proxy/Caddyfile` blocks `/storage/*`; keep
  that rule. It's also reachable on the `local` and `lan` bindings, which have
  no Caddy in front, so don't put real data in multi-user pods there.
- **Invite-only.** The `internet` profile sets `JSS_INVITE_ONLY=true`, so
  `POST /.pods` needs an invite code (`jss invite create` inside the container).
- **Long-lived tokens.** `POST /.pods` returns a long-lived `token` for the new
  account. Don't log it or paste it anywhere; if it leaks, change the account's
  password (`jss passwd <user>` inside the container) or recreate the account.
- **Secrets volume.** `jss-secrets` holds `token.secret`; anyone with it can
  mint tokens. Don't share or publish volume exports.
- **Backups.** All data is in the `jss-data` and `jss-secrets` volumes. Back
  both up while the pod is stopped:

  ```bash
  make down && podman volume export jss-data -o jss-data.tar && podman volume export jss-secrets -o jss-secrets.tar && make up PROFILE=internet
  ```

  Restore with `podman volume import <volume> <file>.tar`.

## Upgrading JSS

1. Change `ARG JSS_VERSION=...` in `jss/Containerfile` (check
   `npm view javascript-solid-server version`).
2. `make rebuild` (add `PROFILE=...` if you're not on `local`).
3. Check whether the new version still exposes `/storage/me/` without WAC
   checks before relaxing the Caddy rule.

Data and secrets live in volumes, so they survive the rebuild.

## Full removal

```bash
make reset
```

```bash
podman rmi localhost/jss:latest docker.io/library/node:22-bookworm-slim docker.io/library/caddy:2
```

Then delete this folder. If you installed Caddy, remove the JSS block from
`/etc/caddy/Caddyfile` (or `sudo apt remove caddy`).

## License

Copyright (C) 2026 Eric Jahn

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License as published by the Free
Software Foundation, version 3 only (`SPDX-License-Identifier: AGPL-3.0-only`).

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU Affero General Public License for more
details. The full text is in [LICENSE](LICENSE).

JavaScript Solid Server (also AGPL-3.0-only, © Melvin Carvalho), which the
image installs from npm, and the other software this setup uses are licensed
separately by their authors; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
