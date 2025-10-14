.DEFAULT_GOAL := help

.PHONY: help
help: # show help for each of the Makefile recipes
	@grep -E '^[a-zA-Z0-9 -]+:.*#'  Makefile | sort | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done

.PHONY: init
init: # install dependencies
	python3 -m venv venv
	. venv/bin/activate && pip install -e ".[dev]"

.PHONY: dev
dev: init # run in development mode
	. venv/bin/activate && python -m simple_a2a_server --host 0.0.0.0

.PHONY: lint
lint: # run linting and type checking
	flake8 src/simple_a2a_server/
	mypy src/simple_a2a_server/
	black --check src/simple_a2a_server/
	isort --check-only src/simple_a2a_server/

.PHONY: lint-fix
lint-fix: # fix linting issues
	black src/simple_a2a_server/
	isort src/simple_a2a_server/

.PHONY: build
build: # build container
	../../../scripts/build-and-push.sh -i simple-agent

.PHONY: install
install: build # build and deploy
	@sh -c ' \
			set -a; \
			if [ -f .env ]; then . ./.env; fi; \
			set +a; \
			kubectl create secret generic simple-agent-secret \
				--from-literal=server-url="$${A2A_SERVER_URL:-http://simple-agent:8000}" \
				--namespace="$${NAMESPACE:-default}" \
				--dry-run=client -o yaml | kubectl apply -f -; \
			helm upgrade --install simple-agent chart/ \
				--namespace="$${NAMESPACE:-default}" \
				--wait --timeout=60s; \
		'

.PHONY: uninstall
uninstall: # remove resources
	helm uninstall simple-agent --ignore-not-found
	kubectl delete secret simple-agent-secret --ignore-not-found

.PHONY: status
status: # show status
	@kubectl get a2aserver simple-agent -o yaml 2>/dev/null || echo "A2AServer not found"
	@kubectl get agents -l a2a/server=simple-agent 2>/dev/null || echo "No agents found"

.PHONY: logs
logs: # show logs
	kubectl logs -l app=simple-agent --tail=50

.PHONY: port-forward
port-forward: # port forward to local development
	kubectl port-forward service/simple-agent 8000:80

.PHONY: test-local
test-local: # test the agent locally
	@echo "Testing agent discovery..."
	@curl -s http://localhost:8000/.well-known/agent.json | jq .
	@echo "\nTesting health endpoint..."
	@curl -s http://localhost:8000/health | jq .
	@echo "\nTesting A2A execution..."
	@curl -X POST http://localhost:8000/ \
		-H "Content-Type: application/json" \
		-d '{"jsonrpc": "2.0", "method": "execute", "params": {"message": {"parts": [{"text": "Hello, test message"}]}}, "id": 1}' | jq .
