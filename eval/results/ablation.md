# Ablation: retrieval top-k

Same 25-question set and model; only the number of retrieved chunks (k) changes.

| k | Groundedness | Citation accuracy | Partial match | Latency p50 | Latency p95 |
|--:|--:|--:|--:|--:|--:|
| 4 | 96.0% | 92.0% | 100.0% | 6157.0 ms | 8195.4 ms |
| 6 | 88.0% | 88.0% | 100.0% | 8152.0 ms | 10215.6 ms |
