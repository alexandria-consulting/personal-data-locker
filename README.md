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
| `proxy/Caddyfile` | Host-side Caddy reverse proxy (internet and LAN `tls internal` examples) |
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
| `make down` | Stop and remove the pod (volumes are kept) |
| `make restart` | `down` then `up` |
| `make logs` | Follow server logs |
| `make status` | Show pod, container, and volume state |
| `make shell` | Shell inside the server container |
| `make rebuild` | Rebuild the image without cache, then restart |
| `make reset` | Stop the pod and, after confirmation, delete all data and secrets |

## Create a pod (account)

With the server up on the local profile:

```bash
curl -X POST http://localhost:4443/.pods \
  -H 'Content-Type: application/json' \
  -d '{"name":"eric","email":"eric@example.com","password":"choose-a-password"}'
```

The WebID is `http://localhost:4443/eric/profile/card.jsonld#me` and the pod
root is `http://localhost:4443/eric/`.

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
--configmap`. Its variables become the container's environment.

- **local**: issuer `http://localhost:4443/`, bound to 127.0.0.1.
- **lan**: issuer `http://CHANGE-ME.local:4443/`, bound to 0.0.0.0. Browsers only
  allow Solid-OIDC login over HTTPS or on localhost, so for LAN logins use Caddy
  with `tls internal` and switch the issuer to the `https://` URL.
- **internet**: issuer `https://pod.example.com/`, bound to 127.0.0.1 behind
  Caddy, `JSS_INVITE_ONLY=true`, log level `warn`.

`JSS_IDP_ISSUER` must exactly match the URL clients use to reach the server
(scheme, host, port, trailing slash). If it doesn't, tokens are issued for the
wrong issuer and logins fail. Edit the profile and run `make restart` after
changing it.

## HTTPS with Caddy

Caddy runs on the host because rootless Podman can't bind ports below 1024 by
default.

```bash
sudo apt install -y caddy
```

Put the relevant block from `proxy/Caddyfile` into `/etc/caddy/Caddyfile`
(replacing `pod.example.com` with your domain), then:

```bash
sudo systemctl reload caddy
```

```bash
make up PROFILE=internet
```

## Granting access to an external WebID

To let `https://alexandriaconsulting.com/files/eric_jahn.rdf#me` read, write,
and control a container, PUT an ACL next to it, e.g. for `/eric/shared/`:

```bash
curl -X PUT http://localhost:4443/eric/shared/.acl \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: text/turtle' \
  --data-binary @- <<'EOF'
@prefix acl: <http://www.w3.org/ns/auth/acl#> .

<#owner>
    a acl:Authorization ;
    acl:agent <http://localhost:4443/eric/profile/card.jsonld#me> ;
    acl:accessTo <./> ;
    acl:default <./> ;
    acl:mode acl:Read, acl:Write, acl:Control .

<#eric-external>
    a acl:Authorization ;
    acl:agent <https://alexandriaconsulting.com/files/eric_jahn.rdf#me> ;
    acl:accessTo <./> ;
    acl:default <./> ;
    acl:mode acl:Read, acl:Write, acl:Control .
EOF
```

Keep the local owner rule so you don't lock yourself out. To actually log in as
the external WebID, that profile document must declare a `solid:oidcIssuer`
(pointing at an identity provider that issues tokens for it) and be served with
an RDF content type (e.g. `text/turtle` or `application/rdf+xml`), otherwise
Solid-OIDC clients can't discover the issuer.

## Upgrading JSS

1. Change `ARG JSS_VERSION=...` in `jss/Containerfile` (check
   `npm view javascript-solid-server version`).
2. `make rebuild` (add `PROFILE=...` if you're not on `local`).

Data and secrets live in volumes, so they survive the rebuild.

## Full removal

```bash
make reset
```

```bash
podman rmi localhost/jss:latest docker.io/library/node:22-bookworm-slim
```

Then delete this folder. If you installed Caddy, remove the JSS block from
`/etc/caddy/Caddyfile` (or `sudo apt remove caddy`).
