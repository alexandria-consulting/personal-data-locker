# Personal data locker (JSS on Podman)

A contained development install of the [JavaScript Solid Server](https://jss.live/)
(npm `javascript-solid-server`). Everything runs inside a Podman pod; nothing is
installed on the host except Podman (and, optionally, Caddy for HTTPS).

## Contents

- [Layout](#layout)
- [Install (Ubuntu)](#install-ubuntu)
- [Running](#running)
  - [With make](#with-make)
  - [Running without make](#running-without-make)
  - [Is it running?](#is-it-running)
- [Create a pod (account)](#create-a-pod-account)
- [Get a token and write a resource](#get-a-token-and-write-a-resource)
- [Profiles](#profiles)
- [HTTPS with Caddy](#https-with-caddy)
- [Granting access to an external WebID](#granting-access-to-an-external-webid)
- [Security notes for going public](#security-notes-for-going-public)
- [Upgrading JSS](#upgrading-jss)
- [Full removal](#full-removal)
- [License](#license)

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
| `scripts/create-pod.sh` | Create a pod with a generated password, saving the login outside the repo |
| `scripts/grant-webid.sh` | Grant a WebID access to a container, keeping existing ACL rules |
| `Makefile` | Build / run / inspect / reset commands |

## Install (Ubuntu)

```bash
sudo apt install -y podman make
```

## Running

Run `make` and the `podman` commands below from the root of the install
directory, the folder containing `jss.yaml` and the `Makefile` (here,
`/home/eric/git/personal-data-locker-test`). They use relative paths such as
`jss/`, `profiles/` and `jss.yaml`, so they fail from anywhere else.

### With make

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
| `make create-pod NAME=…` | Create a pod (account) and save its login to `~/.config/jss-dev/<name>-account.txt` |
| `make grant-webid POD=… CONTAINER=… WEBID=…` | Give a WebID Read/Write/Control on a container |

Pass the same `PROFILE=` to `restart` and `rebuild` that you used for `up`.

### Running without make

Without make, the equivalents are `podman kube play --replace --configmap profiles/local.yaml --publish 127.0.0.1:4443:4443 jss.yaml` to start and `podman kube down jss.yaml` to stop.
Build the image first with `podman build -t localhost/jss:latest jss`
(`make up` does this for you). For another profile, use
`profiles/<name>.yaml` (or your `profiles/<name>.local.yaml`) and its bind:
`--publish 0.0.0.0:4443:4443` for `lan`, `--publish 127.0.0.1:4443:4443` for
`local` and `internet`.

### Is it running?

With make:

```bash
make status
```

The `jss` pod should show `Running` and `jss-server` should show `Up`, with
`127.0.0.1:4443->4443/tcp` (or `0.0.0.0:4443` on the `lan` profile). `Exited`
or no pod at all means it's stopped. `make logs` follows the server log.

Without make:

```bash
podman pod ps
```

```bash
podman ps --all --filter name=jss-server
```

Look for `Running` (pod) and `Up …` (container); `Exited` means it stopped.
Follow the log with:

```bash
podman logs -f jss-server
```

Either way, check that it answers HTTP:

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:4443/
```

`200` means it's up; `000` means nothing is listening on port 4443. You can
also open <http://localhost:4443/> in a browser.

The pod doesn't start again by itself after a reboot (rootless Podman doesn't
start pods at boot unless you set that up), so after restarting the machine,
run `make up` again. Your data is kept in the `jss-data` and `jss-secrets`
volumes.

## Create a pod (account)

With the server up on the local profile, create a pod (account) named `your_pod_username`:

```bash
make create-pod NAME=your_pod_username
```

```text
WebID:   http://localhost:4443/your_pod_username/profile/card.jsonld#me
Pod:     http://localhost:4443/your_pod_username/
Login:   /home/eric/.config/jss-dev/your_pod_username-account.txt
```

`scripts/create-pod.sh` generates a random password, calls `POST /.pods`, and
saves the login to `~/.config/jss-dev/<name>-account.txt` (folder mode 700,
file mode 600, outside the repo) as `email=`, `password=`, `webid=` and `pod=`
lines. That's where `make grant-webid` and the examples below look for it. The
email defaults to `<name>@localhost`; pass `EMAIL=…` to change it. It never
prints the password or the long-lived token that `POST /.pods` returns, and it
refuses to overwrite an existing account file.

To read the password back:

```bash
sed -n 's/^password=//p' ~/.config/jss-dev/your_pod_username-account.txt
```

Accounts created so far on this machine's local server:

| Pod | WebID | Login file |
| --- | --- | --- |
| `test` | `http://localhost:4443/test/profile/card.jsonld#me` | `~/.config/jss-dev/test-account.txt` |

The test account's login is saved in `~/.config/jss-dev/test-account.txt`.

The raw API call, if you'd rather do it by hand (the response includes a
long-lived `token`; treat it like a password):

```bash
curl -X POST http://localhost:4443/.pods \
  -H 'Content-Type: application/json' \
  -d '{"name":"eric","email":"eric@example.com","password":"choose-a-password"}'
```

## Get a token and write a resource

```bash
F=~/.config/jss-dev/your_pod_username-account.txt
TOKEN=$(jq -n --arg e "$(sed -n 's/^email=//p' $F)" --arg p "$(sed -n 's/^password=//p' $F)" '{email: $e, password: $p}' \
  | curl -s -X POST http://localhost:4443/idp/credentials -H 'Content-Type: application/json' --data-binary @- \
  | jq -r .access_token)
```

```bash
curl -X PUT http://localhost:4443/your_pod_username/notes/hello.txt \
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
It also blocks `/storage/*` and `POST /.pods` (see [Security](#security-notes-for-going-public)).

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

5. Create accounts with `make create-pod NAME=…` on this machine (it talks to
   `localhost:4443` directly; Caddy returns 403 for `POST /.pods`, see
   [Security](#security-notes-for-going-public)), or hand out invite codes for
   the IdP sign-up form at `/idp/register`, which stays open and enforces them:

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
- **Invite-only covers the sign-up form, not the API.** The `internet` profile
  sets `JSS_INVITE_ONLY=true`, so the IdP's sign-up form needs an invite code
  (`jss invite create` inside the container). But in JSS 0.0.224 the
  `POST /.pods` API doesn't check invites (and its declared one-per-IP-per-day
  limit wasn't enforced in testing), so anyone who can reach it can create
  accounts. `proxy/Caddyfile` therefore answers `POST /.pods` with 403; create
  accounts from this machine with `make create-pod`, which talks to
  `http://localhost:4443` directly and doesn't go through Caddy.
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
