## n8n Service

### General guidelines
- This service deploys the official n8n Docker image
- No custom code - uses upstream n8n directly
- Configuration via environment variables and Helm values

### Deployment
- Uses official n8n image: `docker.n8n.io/n8nio/n8n`
- Persistent storage for workflow data
- Integrated with localhost-gateway for routing
- Pre-configured with ARK API URL

### Development
- To test changes to chart: `make n8n-uninstall && make n8n-install`
- To view logs: `kubectl logs -n default -l app=n8n -f`
- To access shell: `kubectl exec -n default -it deployment/n8n -- sh`

### Making changes
- Chart templates in `chart/templates/`
- Default values in `chart/values.yaml`
- Build configuration in `build.mk`
