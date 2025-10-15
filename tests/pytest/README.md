The test suite performs a complete ARK workflow:
1. **Virtual Environment Setup** - Creates isolated Python environment
2. **OpenJDK Setup** - Checks and configures OpenJDK if needed
3. **ARK Installation** - Installs ARK platform and CLI
4. **Pods Verification** - Verifies three required ARK pods are running (ark-api, ark-dashboard, ark-mcp)
5. **Dashboard Verification** - Starts ARK dashboard and tests HTTP accessibility on common ports
6. **Cleanup** - Removes all resources and virtual environment


Clean up everything and start fresh:
```bash
# Clean up test artifacts
rm -rf .pytest_cache __pycache__ venv

# Run tests
python3 -m pytest test_complete_ark_workflow.py -sv