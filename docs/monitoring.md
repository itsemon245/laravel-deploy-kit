# Monitoring

Monitoring support is opt-in.

## Intended Pieces

- Promtail for log shipping.
- Loki as a log destination.
- Grafana dashboards outside this public kit.
- Optional app health endpoint checks during deploy.
- Optional Promtail bootstrap through the monitoring role.

## Public Vs Private Values

Keep these private:

- real Loki URLs,
- tenant IDs,
- basic auth credentials,
- internal labels that reveal topology,
- alert routing secrets.

Use placeholder endpoints such as `https://loki.monitoring.invalid` in public examples.

## Deployment Contract

Monitoring templates should consume explicit manifest values and secret classes. Monitoring credentials belong in the `monitoring` class, not the Laravel app `.env`.
