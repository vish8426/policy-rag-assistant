# RAG Evaluation Results

- Model: `llama-3.1-8b-instant`  |  Embeddings: `sentence-transformers/all-MiniLM-L6-v2`  |  Top-k: 4  |  Re-rank: True
- Questions: 25

## Summary

| Metric | Value |
|---|---|
| Groundedness | 96.0% |
| Citation accuracy | 92.0% |
| Partial match (gold fact) | 100.0% |
| Latency p50 | 6157.0 ms |
| Latency p95 | 8195.4 ms |
| Latency mean | 5574.1 ms |

## Per-question results

| # | Question | Expected | Cited | Cite | Grnd | Match | Latency |
|--:|---|---|---|:--:|:--:|:--:|--:|
| 1 | How many PTO days do full-time employees get each year? | HR-002 | HR-002 | Y | Y | Y | 391 ms |
| 2 | What is the monthly PTO accrual rate? | HR-002 | HR-002 | Y | Y | Y | 106 ms |
| 3 | How many unused PTO days can I carry over to the next year? | HR-002 | HR-002 | Y | Y | Y | 118 ms |
| 4 | How many paid sick days do full-time employees receive? | HR-002 | HR-002 | Y | Y | Y | 4138 ms |
| 5 | How long is paid parental leave? | HR-002 | HR-002 | Y | Y | Y | 12258 ms |
| 6 | How many paid days of bereavement leave are provided for an immediate family member? | HR-002 | HR-002 | Y | Y | Y | 8205 ms |
| 7 | How many paid company holidays does Helix observe? | HR-007 | HR-002 | N | Y | Y | 7162 ms |
| 8 | How many floating holidays do employees get each year? | HR-007 | HR-007, HR-010 | Y | Y | Y | 5142 ms |
| 9 | What is the meal per diem for domestic travel? | FIN-001 | FIN-001, FIN-002 | Y | Y | Y | 5199 ms |
| 10 | Above what amount is a receipt required for expenses? | FIN-001 | FIN-001 | Y | Y | Y | 6157 ms |
| 11 | Within how many days must expenses be submitted? | FIN-001 | FIN-001 | Y | Y | Y | 6171 ms |
| 12 | What expense amount can a direct manager approve? | FIN-001 | FIN-001, FIN-003 | Y | Y | Y | 6189 ms |
| 13 | When can employees book business or premium economy class flights? | FIN-002 | FIN-002 | Y | Y | Y | 7151 ms |
| 14 | Is first-class airfare reimbursable? | FIN-002 | FIN-001, FIN-002 | Y | Y | Y | 6180 ms |
| 15 | What is the standard nightly hotel cap in most U.S. cities? | FIN-002 | FIN-002 | Y | Y | Y | 5118 ms |
| 16 | Is multi-factor authentication required for company accounts? | SEC-001 | SEC-001 | Y | Y | Y | 5114 ms |
| 17 | What is the minimum password length? | SEC-001 | SEC-001 | Y | Y | Y | 5102 ms |
| 18 | Who should I contact to report a suspected phishing email? | SEC-001 | SEC-001 | Y | Y | Y | 5141 ms |
| 19 | What is the one-time home office setup stipend? | HR-003 | FIN-001 | N | Y | Y | 6158 ms |
| 20 | What is the annual remote work stipend? | HR-003 | HR-003 | Y | Y | Y | 8157 ms |
| 21 | What does Helix match on the 401(k)? | HR-004 | HR-004 | Y | Y | Y | 6406 ms |
| 22 | What is the annual learning and development budget? | HR-004 | HR-004 | Y | Y | Y | 5127 ms |
| 23 | How much notice should I give when resigning? | HR-005 | HR-005 | Y | Y | Y | 6126 ms |
| 24 | How long after my last day do I have to return company equipment? | HR-005 | HR-005 | Y | Y | Y | 6167 ms |
| 25 | How quickly does Helix respond to a verified data subject request? | SEC-003 | SEC-003 | Y | N | Y | 6170 ms |
