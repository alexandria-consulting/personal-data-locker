# Contained JavaScript Solid Server, run with Podman.
# Usage: make up [PROFILE=local|lan|internet]

PROFILE ?= local
IMAGE   := localhost/jss:latest
CONTAINER := jss-server

ifeq ($(PROFILE),lan)
BIND := 0.0.0.0:4443:4443
else
BIND := 127.0.0.1:4443:4443
endif

.PHONY: build up down restart logs status shell reset rebuild

build:
	podman build -t $(IMAGE) jss

up: build
	podman kube play --replace \
		--configmap profiles/$(PROFILE).yaml \
		--publish $(BIND) \
		jss.yaml

down:
	podman kube down jss.yaml

restart: down up

logs:
	podman logs -f $(CONTAINER)

status:
	podman pod ps --filter name=jss
	podman ps --all --filter pod=jss
	podman volume ls --filter name=jss-

shell:
	podman exec -it $(CONTAINER) sh

reset:
	-podman kube down jss.yaml
	@printf 'This permanently deletes volumes jss-data and jss-secrets (all pods, users, and logins). Type "yes" to continue: '; \
	read answer; [ "$$answer" = "yes" ] || { echo "Aborted."; exit 1; }
	podman volume rm jss-data jss-secrets

rebuild:
	podman build --no-cache -t $(IMAGE) jss
	$(MAKE) restart PROFILE=$(PROFILE)
