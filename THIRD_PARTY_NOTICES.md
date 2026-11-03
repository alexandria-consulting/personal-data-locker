# Third-party notices

This repository holds configuration only: a Containerfile, a Kubernetes Pod
definition, ConfigMap profiles, a Caddyfile, a Makefile, a helper script and
documentation. Those files are Copyright (C) 2026 Eric Jahn and licensed
under the GNU Affero General Public License v3.0 only (`AGPL-3.0-only`); the
full text is in `LICENSE`.

It contains **no source code from JavaScript Solid Server or any other
third-party project**. JSS and the other software below are downloaded from
their upstream registries when you build or run the container, under their own
licenses. The API usage examples in `README.md` (`POST /.pods`, Bearer-token
`PUT`) follow the patterns shown in JSS's own README, rewritten for this setup.

*This file is a good-faith summary for attribution, not legal advice.*

## JavaScript Solid Server (JSS)

| | |
| --- | --- |
| Project | JavaScript Solid Server, npm package `javascript-solid-server` |
| Source | <https://github.com/JavaScriptSolidServer/JavaScriptSolidServer> |
| Website | <https://jss.live/> |
| Copyright | Copyright (C) 2025-2026 Melvin Carvalho |
| License | GNU Affero General Public License v3.0 only (`AGPL-3.0-only`) |
| License text | <https://github.com/JavaScriptSolidServer/JavaScriptSolidServer/blob/main/LICENSE> (also in the image at `/usr/local/lib/node_modules/javascript-solid-server/LICENSE`) |
| Version used | `0.0.224`, pinned by `ARG JSS_VERSION` in `jss/Containerfile` |

The container image built from `jss/Containerfile` (`localhost/jss:latest`)
includes JSS, so the image, and any copy of it you distribute, is governed by
the AGPL-3.0 for the JSS parts. In particular:

- **Distributing the image** (pushing it to a registry, giving it to others)
  means passing on the AGPL-3.0 terms and making the corresponding JSS source
  available.
- **Network use (AGPL §13).** If you modify JSS and let others use it over a
  network, you must offer those users the complete source of your modified
  version. Running an unmodified upstream release, as this repository does,
  is satisfied in practice by pointing to the upstream source and the exact
  version above.
- If you patch JSS (for example to disable its remoteStorage endpoint), keep a
  notice of the change (AGPL §5(a)) and publish the modified source to anyone
  using the server.

The JSS authors also offer commercial licensing for deployments that can't meet
the AGPL terms; see `LICENSING.md` in the JSS repository.

### JSS npm dependencies

`npm install` pulls in 164 packages with JSS 0.0.224 (counted from the
`package.json` license fields inside the built image, 2026-11-02). All are
under permissive licenses; none is copyleft:

| License | Packages |
| --- | --- |
| MIT | 137 |
| Apache-2.0 | 12 (including `mongodb`, `bson`, `bare-*`, `reflect-metadata`) |
| BSD-3-Clause | 6 |
| ISC | 6 |
| 0BSD | 2 |
| BSD-2-Clause | 1 |

Each package's license text ships in its folder under
`/usr/local/lib/node_modules/javascript-solid-server/node_modules/` in the
image. Re-check after upgrading JSS:

```bash
podman exec jss-server sh -c 'cd $(npm root -g)/javascript-solid-server && npm ls --all'
```

## Container base image: Node.js on Debian

| | |
| --- | --- |
| Image | `docker.io/library/node:22-bookworm-slim` (Docker Official Image) |
| Image source | <https://github.com/nodejs/docker-node> (MIT) |
| Node.js | Node.js 22, <https://nodejs.org/>, MIT license; bundles third-party components under their own licenses (see `LICENSE` in the Node.js repository) |
| npm | npm 10, <https://github.com/npm/cli>, Artistic License 2.0, Copyright (c) npm, Inc. and Contributors |
| Corepack | <https://github.com/nodejs/corepack>, MIT |
| Debian | Debian 12 "bookworm" packages, <https://www.debian.org/>, various free licenses; per-package copyright files are in the image under `/usr/share/doc/*/copyright` |

Node.js is a trademark of the OpenJS Foundation. Debian is a registered
trademark of Software in the Public Interest, Inc.

## Caddy

| | |
| --- | --- |
| Project | Caddy web server, <https://caddyserver.com/>, <https://github.com/caddyserver/caddy> |
| License | Apache License 2.0, Copyright Matthew Holt and The Caddy Authors |
| How it's used | Installed on the host by you (`apt install caddy`) to run `proxy/Caddyfile`; `make caddy-validate` runs the `docker.io/library/caddy:2` image (Alpine Linux base, various licenses) only to check syntax |

Caddy is a registered trademark of Stack Holdings GmbH.

## Podman

| | |
| --- | --- |
| Project | Podman, <https://podman.io/>, <https://github.com/containers/podman> |
| License | Apache License 2.0 |
| How it's used | Host tool for building and running the pod; not included in or distributed by this repository |

## Standards and formats referenced

- **Solid Protocol** and **Web Access Control** (ACL vocabulary
  `http://www.w3.org/ns/auth/acl#`), W3C Solid Community Group,
  <https://solidproject.org/TR/>.
- **Kubernetes** Pod and ConfigMap formats used by `jss.yaml` and the profiles
  (<https://kubernetes.io/>). Kubernetes is a registered trademark of The Linux
  Foundation.
