PROJECT := igrant
APP     := pob-backend
NAME    = $(PROJECT)-$(APP)

TERM_FLAGS ?= -ti

EXTRA_RUN_ARGS ?=

VERSION   ?= $(shell git describe --tags --abbrev=0)
CANDIDATE ?= "dev"
CONTAINER_POB_BACKEND ?= "igrant_pob_backend_dev"

CONTAINER_DEFAULT_RUN_FLAGS := \
	--rm $(TERM_FLAGS) \
	$(EXTRA_RUN_ARGS)

GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD | sed -E 's/[^a-zA-Z0-9]+/-/g')
GIT_COMMIT := $(shell git rev-parse --short HEAD)

# jenkins specific
ifdef BRANCH_NAME
    GIT_BRANCH = $(shell echo $(BRANCH_NAME) | tr '[:upper:]' '[:lower:]' | tr -cd '[[:alnum:]]_-')
endif

DEPLOY_VERSION_FILE = ./deploy_version
DEPLOY_VERSION = $(shell test -f $(DEPLOY_VERSION_FILE) && cat $(DEPLOY_VERSION_FILE))

GCLOUD_HOSTNAME = eu.gcr.io
GCLOUD_PROJECTID = jenkins-189019
DOCKER_IMAGE := ${GCLOUD_HOSTNAME}/${GCLOUD_PROJECTID}/$(NAME)

# tag based on git branch, date and commit
DOCKER_TAG := $(GIT_BRANCH)-$(shell date +%Y%m%d%H%M%S)-$(GIT_COMMIT)

DJANGO_SUPERUSER_PASSWORD = admin
DJANGO_SUPERUSER_EMAIL = admin@example.com
DJANGO_SUPERUSER_USERNAME = admin

.DEFAULT_GOAL := help
.PHONY: help
help:
	@echo "------------------------------------------------------------------------"
	@echo "Bolagsverket (Proof Of Business) - Backend"
	@echo "------------------------------------------------------------------------"
	@grep -E '^[0-9a-zA-Z_/%\-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.bootstrap:
	git clone git@github.com:L3-iGrant/bootstrap.git "$(CURDIR)/.bootstrap"
	git --git-dir=$(CURDIR)/.bootstrap/.git --work-tree=$(CURDIR)/.bootstrap checkout cors

.PHONY: bootstrap
bootstrap: .bootstrap ## Boostraps development environment
	git -C $(CURDIR)/.bootstrap fetch --all --prune
	git -C $(CURDIR)/.bootstrap reset --hard origin/cors
	make -C .bootstrap bootstrap

setup: bootstrap ## Sets up development environment

run: ## Run backend locally for development purposes
	docker run \
		$(CONTAINER_DEFAULT_RUN_FLAGS) \
		--expose 8000 \
		-e DJANGO_SUPERUSER_USERNAME="${DJANGO_SUPERUSER_USERNAME}" \
		-e DJANGO_SUPERUSER_EMAIL="${DJANGO_SUPERUSER_EMAIL}" \
		-e DJANGO_SUPERUSER_PASSWORD="${DJANGO_SUPERUSER_PASSWORD}" \
		-v $(CURDIR)/db:/app/db \
		-p 8000:8000 \
		--name "${CONTAINER_POB_BACKEND}" \
		$(DOCKER_IMAGE):dev

.PHONY: build/docker/deployable
build/docker/deployable: ## Builds deployable docker image for preview, staging and production
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) -f resources/docker/Dockerfile .
	echo "$(DOCKER_IMAGE):$(DOCKER_TAG)" > $(DEPLOY_VERSION_FILE)

.PHONY: build/docker/deployable_x86
build/docker/deployable_x86: ## Builds deployable docker image explicitly for x86 architecture
	docker build --platform=linux/amd64 -t $(DOCKER_IMAGE):$(DOCKER_TAG) -f resources/docker/Dockerfile .
	echo "$(DOCKER_IMAGE):$(DOCKER_TAG)" > $(DEPLOY_VERSION_FILE)

.PHONY: build
build: ## Builds the docker image
	docker build -t $(DOCKER_IMAGE):dev -f resources/docker/Dockerfile .

.PHONY: publish
publish: $(DEPLOY_VERSION_F ILE) ## Publish latest production Docker image to docker hub
	gcloud docker -- push $(DEPLOY_VERSION)

deploy/production: $(DEPLOY_VERSION_FILE) ## Deploy to K8s cluster (e.g. make deploy/{preview,staging,production})
	kubectl set image deployment/demo-pob-backend demo-pob-backend=$(DEPLOY_VERSION) -n bolagsverket 

deploy/staging: $(DEPLOY_VERSION_FILE) ## Deploy to K8s cluster (e.g. make deploy/{preview,staging,staging})
	kubectl set image deployment/pob-backend pob-backend=$(DEPLOY_VERSION) -n bolagsverket 

$(DEPLOY_VERSION_FILE):
	@echo "Missing '$(DEPLOY_VERSION_FILE)' file. Run 'make build/docker/deployable'" >&2
	exit 1

