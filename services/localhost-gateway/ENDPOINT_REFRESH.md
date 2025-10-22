# NGINX Gateway Endpoint Refresh

## Problem

NGINX Gateway Fabric uses static IP addresses in upstream configurations instead of DNS-based service discovery. When a pod is restarted and receives a new IP address, the gateway needs to be notified of the endpoint change.

### Root Cause

NGINX Gateway Fabric **does** watch EndpointSlice changes automatically and should reload nginx configuration when endpoints change. However, there are two scenarios where this fails:

1. **Gateway controller not running**: If the gateway controller is down or restarting when an endpoint changes, it misses the update event
2. **Missed reconciliation**: The controller only processes live Kubernetes events - it doesn't always reconcile full state on startup

### Symptoms

- HTTP 502 Bad Gateway errors when accessing services through the gateway
- Nginx logs show `connect() failed (113: Host is unreachable) while connecting to upstream`
- The upstream IP in nginx config (`/etc/nginx/conf.d/http.conf`) doesn't match the current pod IP

## Solutions

### Short-term: Manual Reload

When you encounter 502 errors after pod restarts, force the nginx gateway to refresh:

```bash
make localhost-gateway-reload
```

This command:
1. Deletes the nginx gateway pod
2. Waits for it to restart
3. On startup, the gateway regenerates config with current endpoint IPs

### Long-term: Monitoring and Auto-healing

The proper solution is to ensure the gateway controller is always running and healthy:

1. **Use NGINX Plus** (if available): NGINX Plus supports dynamic upstream updates via API, eliminating the need for reloads when endpoints change

2. **Monitor gateway health**: Add monitoring to alert when the gateway controller is down:
   ```bash
   kubectl get pods -n ark-system -l app.kubernetes.io/name=nginx-gateway-fabric
   ```

3. **Endpoint monitoring**: The gateway should automatically pick up EndpointSlice changes. If it doesn't, check:
   ```bash
   # View gateway controller logs
   kubectl logs -n ark-system -l app.kubernetes.io/name=nginx-gateway-fabric --tail=100

   # Check for endpoint update events
   kubectl logs -n ark-system -l app.kubernetes.io/name=nginx-gateway-fabric | grep -i endpointslice
   ```

## How NGINX Gateway Fabric Should Work

According to the [NGINX Gateway Fabric architecture](https://docs.nginx.com/nginx-gateway-fabric/overview/gateway-architecture/):

- The control plane watches Gateway API resources, Services, Endpoints, and Secrets
- When endpoints change, the controller detects the EndpointSlice update
- It regenerates nginx configuration with updated upstream IPs
- NGINX is reloaded gracefully to apply the changes

**Why it sometimes fails:**
- If the controller pod is restarting during an endpoint change, it may miss the event
- Controller-runtime doesn't always reconcile full state on startup for performance reasons
- No reconciliation loop ensures upstreams match current EndpointSlice state

## Future Improvements

Consider these enhancements to make the system more resilient:

1. **Add reconciliation loop**: Periodically verify nginx upstreams match EndpointSlice IPs
2. **Upgrade to NGINX Plus**: Use dynamic upstream API instead of config reloads
3. **Add health checks**: Monitor for 502 errors and auto-trigger gateway reload
4. **Use StatefulSets**: For services where stable network identity is critical

## References

- [NGINX Gateway Fabric Architecture](https://docs.nginx.com/nginx-gateway-fabric/overview/gateway-architecture/)
- [Upgrade Applications Without Downtime](https://docs.nginx.com/nginx-gateway-fabric/how-to/upgrade-apps-without-downtime/)
- [Kubernetes EndpointSlice](https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/)
