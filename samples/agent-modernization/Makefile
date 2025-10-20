.PHONY: init query query-select clean reset help

help:
	@echo "Available targets:"
	@echo "  make init          - Initialize agents and evaluators"
	@echo "  make query         - Apply all queries"
	@echo "  make query-select  - Select which queries to run interactively"
	@echo "  make clean         - Remove agents and evaluators"
	@echo "  make reset         - Clean all auto-generated evaluations and queries"
	@echo "  make help          - Show this help message"
	@echo ""
	@echo "Individual query targets:"
	@echo "  make query-threading         - Apply java-with-threading-complexity query"
	@echo "  make query-functional        - Apply java8-functional-interfaces query"
	@echo "  make query-stream            - Apply java8-stream-operations query"
	@echo "  make query-malformed         - Apply malformed-java-code query"
	@echo "  make query-python            - Apply non-java-python-code query"

init:
	@echo "Initializing agent-modernization resources..."
	kubectl apply -f agents/
	kubectl apply -f custom-evaluators/
	kubectl apply -f perf-evaluators/
	@echo "Done! Resources initialized."

query:
	@echo "Applying all queries..."
	kubectl apply -f queries/
	@echo "Done! Queries applied."

query-select:
	@echo "Select queries to run:"
	@echo "1) java-with-threading-complexity"
	@echo "2) java8-functional-interfaces"
	@echo "3) java8-stream-operations"
	@echo "4) malformed-java-code"
	@echo "5) non-java-python-code"
	@echo "6) All queries"
	@read -p "Enter numbers separated by spaces (e.g., 1 3 5): " choices; \
	for choice in $$choices; do \
		case $$choice in \
			1) kubectl apply -f queries/query-java-with-threading-complexity.yaml ;; \
			2) kubectl apply -f queries/query-java8-functional-interfaces.yaml ;; \
			3) kubectl apply -f queries/query-java8-stream-operations.yaml ;; \
			4) kubectl apply -f queries/query-malformed-java-code.yaml ;; \
			5) kubectl apply -f queries/query-non-java-python-code.yaml ;; \
			6) kubectl apply -f queries/ ;; \
			*) echo "Invalid choice: $$choice" ;; \
		esac; \
	done

query-threading:
	@echo "Applying java-with-threading-complexity query..."
	kubectl apply -f queries/query-java-with-threading-complexity.yaml

query-functional:
	@echo "Applying java8-functional-interfaces query..."
	kubectl apply -f queries/query-java8-functional-interfaces.yaml

query-stream:
	@echo "Applying java8-stream-operations query..."
	kubectl apply -f queries/query-java8-stream-operations.yaml

query-malformed:
	@echo "Applying malformed-java-code query..."
	kubectl apply -f queries/query-malformed-java-code.yaml

query-python:
	@echo "Applying non-java-python-code query..."
	kubectl apply -f queries/query-non-java-python-code.yaml

clean:
	@echo "Removing agent-modernization resources..."
	kubectl delete -f agents/ --ignore-not-found=true
	kubectl delete -f custom-evaluators/ --ignore-not-found=true
	kubectl delete -f perf-evaluators/ --ignore-not-found=true
	@echo "Done! Resources removed."

reset:
	@echo "Cleaning all auto-generated evaluations and queries..."
	kubectl delete evaluation -l ark.mckinsey.com/auto --ignore-not-found=true
	kubectl delete evaluation -l ark.mckinsey.com/auto=true --ignore-not-found=true
	kubectl delete -f queries/ --ignore-not-found=true
	kubectl delete query -l agent-type=java-modernizer --ignore-not-found=true
	@echo "Done! Auto-generated resources cleaned."
