SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

# Image configuration
IMAGE_NAME = go-task-agent
IMAGE_TAG = latest

.PHONY: help build build-binary test run docker-build docker-run install uninstall clean

help: ## Show this help message
	@echo 'Usage: make [target] ...'
	@echo
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build-binary: ## Build Go binary locally  
	go build -o bin/go-task-agent cmd/main.go

test: ## Run tests
	go test -v ./...

run: build-binary ## Run locally
	./bin/go-task-agent

docker-build: ## Build Docker image
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .

docker-run: docker-build ## Run in Docker container
	docker run -p 8082:8082 $(IMAGE_NAME):$(IMAGE_TAG)

install: docker-build ## Deploy to Kubernetes cluster
	kind load docker-image $(IMAGE_NAME):$(IMAGE_TAG) --name ark || \
	minikube image load $(IMAGE_NAME):$(IMAGE_TAG) || \
	docker tag $(IMAGE_NAME):$(IMAGE_TAG) $(IMAGE_NAME):$(IMAGE_TAG)
	helm upgrade --install go-task-agent ./chart \
		--set image.repository=$(IMAGE_NAME) \
		--set image.tag=$(IMAGE_TAG) \
		--set image.pullPolicy=Never \
		--wait

uninstall: ## Remove from Kubernetes cluster
	helm uninstall go-task-agent || true

clean: ## Clean build artifacts
	rm -rf bin/