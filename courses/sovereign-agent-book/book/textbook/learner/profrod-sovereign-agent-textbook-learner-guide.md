# Your constructed definitions

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

Each file below is the completed comparison implementation for one chapter's construction. Work in your own checkout, and retain your attempts before replacing them with a comparison.

| Chapter | File | What it builds |
| --- | --- | --- |
| 1 | `profrod_sovereign_agent_ch01_model_call_learner.py` | Byte-pair encoding, a bigram model, softmax with temperature, sampling, entropy and perplexity |
| 2 | `profrod_sovereign_agent_ch02_pydantic_shop_tools_learner.py` | Tool schemas, handlers and dispatch |
| 2 | `profrod_sovereign_agent_ch02_constrained_decoding_learner.py` | Validity over length, logit masking, and masked decoding against conditioning on a toy model |
| 3 | `profrod_sovereign_agent_ch03_agent_loop_learner.py` | The owned model and tool loop, its adapter, and the reliability arithmetic |
| 4 | `profrod_sovereign_agent_ch04_state_store_learner.py` | The durable state store |
| 5 | `profrod_sovereign_agent_ch05_retrieval_learner.py` | BM25, cosine similarity, precision@k, recall@k, reciprocal rank and a context packer |
| 6 | `profrod_sovereign_agent_ch06_embeddings_learner.py` | One-hot vectors, the lookup as a matrix product, skip-gram with negative sampling, pooling, exact search, reciprocal rank fusion, ranking metrics and a small-world graph |
| 7 | `profrod_sovereign_agent_ch07_prompt_sensitivity_learner.py` | Labels from free text, accuracy, spread across prompts, case-sampling noise and agreement |
| 7 | `profrod_sovereign_agent_ch07_skills_learner.py` | Strict skill records, bounded reads, immutable staged versions, evaluated activation against a baseline, and skill eligibility in Chapter 5's context |
| 8 | `profrod_sovereign_agent_ch08_work_queue_learner.py` | The durable work queue |
| 9 | `profrod_sovereign_agent_ch09_latency_learner.py` | A least-squares line, prefill as b n + c n², time to first token and to the whole reply, and conversation prefill with and without a cache |
| 9 | `profrod_sovereign_agent_ch09_messaging_learner.py` | The Telegram channel on the Chapter 8 queue: allowlisted private intake committed with its cursor, session-serialized claims, and delivery that denies a removed recipient and never resends an unknown report |
| 10 | `profrod_sovereign_agent_ch10_queueing_learner.py` | Service-time moments, utilization, the Pollaczek–Khinchine wait, the rate for a target wait, Poisson arrivals and rescan delay |
| 10 | `profrod_sovereign_agent_ch10_wakeups_learner.py` | Fixed-interval jobs that coalesce missed runs, stock conditions that admit one piece of work per shortage episode, strict admission that stores nothing when the queue is full, a work subject that scopes the shop tools, reports built from draft observations, and an unattended serving loop |
| 11 | `profrod_sovereign_agent_ch11_calibration_learner.py` | The reorder rule, expected calibration error, auto-approval coverage and error, agreement confidence and the approval threshold |
| 12 | `profrod_sovereign_agent_ch12_retries_learner.py` | Attempts and duplicate effects of retries, capped attempts under timeouts, percentiles, a stable operation key, and a proxy that loses a committed order's reply |
| 13 | `profrod_sovereign_agent_ch13_leases_learner.py` | False expiry from turn lengths, the shortest safe lease, detection delay and the fencing rule |
| 15 | `profrod_sovereign_agent_ch15_injection_learner.py` | Attempted-action checks, attack success rates with intervals, and spotlighting |
| 15 | `profrod_sovereign_agent_ch15_isolation_learner.py` | An untrusted document tool, a catalog reached through the Chapter 14 client with discovery kept apart from permission, a worker whose dispatcher registers no purchase tool, and model-written Python run under the OS sandbox (Seatbelt or bubblewrap) with a trusted supervisor's deadline, refused where no sandbox exists |
| 15 | `profrod_sovereign_agent_ch15_catalog_server.py` | A standard-library MCP server over stdio: Lucy's catalog, and a purchase tool whose description claims authority it does not have |
| 16 | `profrod_sovereign_agent_ch16_evaluation_statistics_learner.py` | Wilson intervals, clustered standard errors, McNemar's test, sample size, pass@k and kappa |
| 17 | `profrod_sovereign_agent_ch17_optimization_learner.py` | The expected maximum of k normals, the winner's curse, and Bradley–Terry ratings fitted from preferences |
| 17 | `profrod_sovereign_agent_ch17_improvement_learner.py` | Attributed proposals staged through Chapter 7, the change operation over Chapter 16's harness that saves its report before switching, rollback that must re-earn activation, and the STALE guard |
| 18 | `profrod_sovereign_agent_ch18_delegation_learner.py` | Amdahl's law, composed success, majority-vote accuracy and delegation token counts; one bounded delegation with an immutable contract, role-separated claims, fenced model calls billed to the parent, cancellation and expiry |
| 19 | `profrod_sovereign_agent_ch19_inference_economics_learner.py` | Decode ceilings, arithmetic intensity, KV-cache memory, latency, percentiles, Little's law and loop cost |
| 19 | `profrod_sovereign_agent_ch19_operations_learner.py` | A consistent SQLite backup; a restore that keeps the file, starts paused and revokes every old approval and lease; a read-only health summary; account inspection that fences the supplier; a digest-bound recovery plan of current counts and deliveries; and the systemd unit for the Chapter 10 worker |
| 19 | `profrod_sovereign_agent_ch19_supplier_learner.py` | Chapter 11's supplier with an account epoch that every order must carry, and a complete receipt export for recovery |
| 20 | `profrod_sovereign_agent_ch20_reliability_learner.py` | Series success, per-step reliability, the Wilson interval, and checks of a report's amounts and names |
| 20 | `profrod_sovereign_agent_ch20_day_learner.py` | Every earlier chapter's store opened as one; a worker that handles phone approvals and order continuations without a model and model turns that may propose orders and then wait; retries as new work; delivery received once; and a report read from one snapshot |

Each chapter's checkpoint loads its file, so changing a function's essential behavior changes the executable result. The live adapters still use supplied bounded HTTP transport, and later reference checkpoints import other supplied runtime components. See [code ownership](https://profrod.ai/book/code-ownership) and the [construction roadmap](https://profrod.ai/book/construction-roadmap) before treating these files as a finished agent.

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
