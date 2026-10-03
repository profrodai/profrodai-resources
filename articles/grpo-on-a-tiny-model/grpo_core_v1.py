# Prof Rod | GRPO on a Tiny Model
# Article: https://profrod.ai/articles/grpo-on-a-tiny-model
# Original source and updates: https://github.com/profrodai/profrodai-resources

"""GRPO in plain PyTorch. `transformers` supplies only the model and its tokenizer.

The objective (DeepSeekMath, Shao et al. 2024, eq. 3), for a prompt q and a group of G responses
o_1..o_G sampled from the policy that was current when they were drawn (pi_old):

    J(theta) = mean_i  1/|o_i| sum_t [ min(rho_it A_i, clip(rho_it, 1-eps, 1+eps) A_i) - beta KL_it ]

How each term arrives, one step at a time:

1. REINFORCE. grad E_{o~pi}[r(o)] = E[r(o) grad log pi(o)], because grad pi = pi grad log pi. With
   log pi(o) = sum_t log pi(o_t | q, o_<t), each token's log-probability is pushed up in proportion
   to the whole response's reward.
2. A baseline. E[b grad log pi(o)] = b grad sum_o pi(o) = b grad 1 = 0 for any b that does not
   depend on o, so r can be replaced by r - b without biasing the gradient; a good b cuts variance.
   PPO learns b with a value network. GRPO drops the critic: b is the mean reward of the G responses
   to the same prompt, and dividing by their standard deviation puts every prompt on one scale:
       A_i = (r_i - mean(r_1..r_G)) / (std(r_1..r_G) + delta).
   A group whose responses all score the same gives A = 0: that prompt teaches nothing this step.
3. Importance ratio and the clip. Responses come from pi_old, but after the first optimizer step
   we are differentiating pi_theta. E_{pi_old}[rho A grad log pi_theta], rho = pi_theta/pi_old per
   token, corrects for that. If rho drifts far from 1 the estimate is noisy, so PPO takes the
   pessimistic min of the ratio term and its clipped copy: once the ratio has moved by eps in the
   direction the advantage favors, that token's gradient is zero.
4. KL to the reference. beta * KL(pi_theta || pi_ref) keeps the policy near the starting model, so
   it does not forget how to write while chasing reward. Per token it uses the unbiased,
   always-nonnegative estimator k3 (Schulman 2020): with x = pi_ref/pi_theta on the sampled token,
   KL_t = x - log x - 1. E_{pi_theta}[x] = 1, so its mean is E[-log x], the KL itself.
5. The 1/|o_i| average gives each response equal weight whatever its length. That is the original
   GRPO choice; it also biases toward long wrong answers and short right ones (Liu et al. 2025,
   "Dr. GRPO"), one of the debugging lessons.

Everything here is batch arithmetic over token log-probabilities; see `grpo_loss`.
"""

from __future__ import annotations

import time

import torch


def pick_device(name: str | None = None) -> str:
    if name:
        return name
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def load(model_id: str, revision: str | None, device: str, dtype=torch.float32):
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(model_id, revision=revision)
    model = AutoModelForCausalLM.from_pretrained(
        model_id, revision=revision, dtype=dtype
    ).to(device)
    model.config.use_cache = True
    return model, tok


def encode_prompts(tok, prompts: list[str]) -> list[list[int]]:
    ids = []
    for p in prompts:
        out = tok.apply_chat_template(
            [{"role": "user", "content": p}], add_generation_prompt=True, tokenize=True
        )
        ids.append(list(out["input_ids"] if hasattr(out, "keys") else out))
    return ids


def stop_ids(tok) -> list[int]:
    ids = {tok.eos_token_id}
    for t in ("<|im_end|>", "<|endoftext|>"):
        i = tok.convert_tokens_to_ids(t)
        if isinstance(i, int) and i != tok.unk_token_id:
            ids.add(i)
    return sorted(i for i in ids if i is not None)


def pad_id(tok) -> int:
    return tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id


@torch.no_grad()
def sample(
    model,
    prompts: list[list[int]],
    max_new: int,
    temperature: float,
    pad: int,
    stops: list[int],
) -> list[list[int]]:
    """Autoregressive sampling with a KV cache, written out so the rollout's cost is visible.

    Prompts are left-padded so every row's next token sits in the last column. temperature 0 is
    greedy (for evaluation); temperature 1 samples from the policy exactly, which GRPO requires: the
    log-probabilities in the loss must belong to the distribution the tokens came from.
    Returns each response's token ids, up to and including its stop token.
    """
    device = next(model.parameters()).device
    n, width = len(prompts), max(len(p) for p in prompts)
    ids = torch.full((n, width), pad, dtype=torch.long)
    mask = torch.zeros((n, width), dtype=torch.long)
    for i, p in enumerate(prompts):
        ids[i, width - len(p) :] = torch.tensor(p)
        mask[i, width - len(p) :] = 1
    ids, mask = ids.to(device), mask.to(device)
    positions = (mask.cumsum(-1) - 1).clamp(min=0)
    stop_t = torch.tensor(stops, device=device)
    out = model(
        input_ids=ids,
        attention_mask=mask,
        position_ids=positions,
        use_cache=True,
        logits_to_keep=1,
    )
    past, logits = out.past_key_values, out.logits[:, -1, :].float()
    done = torch.zeros(n, dtype=torch.bool, device=device)
    tokens = []
    pos = positions[:, -1:]
    for _ in range(max_new):
        if temperature == 0:
            nxt = logits.argmax(-1)
        else:
            nxt = torch.multinomial(torch.softmax(logits / temperature, -1), 1).squeeze(
                -1
            )
        nxt = torch.where(done, torch.full_like(nxt, pad), nxt)
        tokens.append(nxt)
        done = done | torch.isin(nxt, stop_t)
        if bool(done.all()):
            break
        mask = torch.cat([mask, torch.ones((n, 1), dtype=mask.dtype, device=device)], 1)
        pos = pos + 1
        out = model(
            input_ids=nxt[:, None],
            attention_mask=mask,
            position_ids=pos,
            past_key_values=past,
            use_cache=True,
        )
        past, logits = out.past_key_values, out.logits[:, -1, :].float()
    gen = torch.stack(tokens, 1).tolist()
    responses = []
    stop_set = set(stops)
    for row in gen:
        r = []
        for t in row:
            r.append(t)
            if t in stop_set:
                break
        responses.append(r)
    return responses


def pack(prompts: list[list[int]], responses: list[list[int]], pad: int, device: str):
    """One tensor batch: prompts left-padded to P, responses right-padded to R.

    Returns input_ids [N, P+R], attention_mask, position_ids, the response ids [N, R] and a 0/1
    response mask [N, R]. Token k of a response sits at position P+k and is predicted by the
    logits at position P+k-1.
    """
    n = len(prompts)
    P, R = max(len(p) for p in prompts), max(1, max(len(r) for r in responses))
    ids = torch.full((n, P + R), pad, dtype=torch.long)
    att = torch.zeros((n, P + R), dtype=torch.long)
    rmask = torch.zeros((n, R), dtype=torch.float32)
    for i, (p, r) in enumerate(zip(prompts, responses)):
        ids[i, P - len(p) : P] = torch.tensor(p)
        att[i, P - len(p) : P] = 1
        if r:
            ids[i, P : P + len(r)] = torch.tensor(r)
            att[i, P : P + len(r)] = 1
            rmask[i, : len(r)] = 1
    pos = (att.cumsum(-1) - 1).clamp(min=0)
    return {
        "input_ids": ids.to(device),
        "attention_mask": att.to(device),
        "position_ids": pos.to(device),
        "response_ids": ids[:, P:].to(device),
        "response_mask": rmask.to(device),
        "R": R,
    }


def token_logprobs(model, batch: dict, rows: slice, entropy: bool = False):
    """log pi(o_t | q, o_<t) for every response token in `rows`, and optionally the entropy of pi at
    each of those positions. Only the last R+1 positions' logits are computed: the vocabulary is
    151,936 wide for Qwen, so full-sequence logits would dominate memory."""
    R = batch["R"]
    out = model(
        input_ids=batch["input_ids"][rows],
        attention_mask=batch["attention_mask"][rows],
        position_ids=batch["position_ids"][rows],
        use_cache=False,
        logits_to_keep=R + 1,
    )
    logits = out.logits[:, :-1, :].float()  # [m, R, V]: predicts response tokens 0..R-1
    target = batch["response_ids"][rows]
    lse = torch.logsumexp(logits, -1)
    logp = logits.gather(-1, target[..., None]).squeeze(-1) - lse
    if not entropy:
        return logp, None
    probs = torch.softmax(logits, -1)
    ent = lse - (probs * logits).sum(-1)  # H = -sum p log p = logsumexp(z) - sum p z
    return logp, ent


def group_advantages(
    rewards: torch.Tensor, group: int, delta: float = 1e-4
) -> torch.Tensor:
    """A_i = (r_i - mean of its group) / (std of its group + delta). rewards: [B*G], grouped
    contiguously. Population std (unbiased=False): the group is the whole sample being normalized."""
    r = rewards.view(-1, group)
    a = (r - r.mean(1, keepdim=True)) / (r.std(1, keepdim=True, unbiased=False) + delta)
    return a.view(-1)


def grpo_loss(logp, old_logp, ref_logp, adv, mask, clip_eps: float, beta: float):
    """The negative GRPO objective for a minibatch, and its diagnostics. All tensors [m, R] except
    adv [m]. Returns (loss, stats) with loss already averaged as in the docstring at the top."""
    ratio = torch.exp(logp - old_logp)  # rho = pi_theta / pi_old, per token
    a = adv[:, None]
    surrogate = torch.min(ratio * a, torch.clamp(ratio, 1 - clip_eps, 1 + clip_eps) * a)
    log_x = ref_logp - logp  # x = pi_ref / pi_theta
    kl = torch.exp(log_x) - log_x - 1  # k3 >= 0, unbiased for KL(pi_theta || pi_ref)
    per_token = -(surrogate - beta * kl)
    lengths = mask.sum(1).clamp(min=1)
    loss = ((per_token * mask).sum(1) / lengths).mean()
    with torch.no_grad():
        clipped = ((ratio - 1).abs() > clip_eps).float()
        stats = {
            "kl": float((kl * mask).sum() / mask.sum()),
            "clipFraction": float((clipped * mask).sum() / mask.sum()),
        }
    return loss, stats


class LoRALinear(torch.nn.Module):
    """y = W x + (alpha / r) B A x, with W frozen. B starts at zero, so the adapted model starts
    exactly at the base model; only A and B (r * (in + out) numbers per layer) are trained.
    `enabled = False` gives back the base model, which serves as the frozen reference for the KL
    term without a second copy of the weights."""

    def __init__(self, base: torch.nn.Linear, r: int, alpha: float):
        super().__init__()
        self.base, self.scale, self.enabled = base, alpha / r, True
        self.A = torch.nn.Parameter(
            torch.empty(
                r, base.in_features, device=base.weight.device, dtype=torch.float32
            )
        )
        self.B = torch.nn.Parameter(
            torch.zeros(
                base.out_features, r, device=base.weight.device, dtype=torch.float32
            )
        )
        torch.nn.init.kaiming_uniform_(self.A, a=5**0.5)

    def forward(self, x):
        y = self.base(x)
        if not self.enabled:
            return y
        return y + (x.to(self.A.dtype) @ self.A.T @ self.B.T * self.scale).to(y.dtype)


LORA_TARGETS = (
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
)


def add_lora(model, r: int, alpha: float) -> int:
    """Freeze the model and wrap every attention and MLP projection with a LoRA adapter. Returns the
    number of trainable parameters."""
    for p in model.parameters():
        p.requires_grad_(False)
    for name, module in list(model.named_modules()):
        for child_name, child in list(module.named_children()):
            if child_name in LORA_TARGETS and isinstance(child, torch.nn.Linear):
                setattr(module, child_name, LoRALinear(child, r, alpha))
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


class adapters_off:
    """Context manager: the LoRA model behaves as its frozen base (the reference policy)."""

    def __init__(self, model):
        self.mods = [m for m in model.modules() if isinstance(m, LoRALinear)]

    def __enter__(self):
        for m in self.mods:
            m.enabled = False

    def __exit__(self, *exc):
        for m in self.mods:
            m.enabled = True


class Timer:
    def __init__(self, device: str):
        self.device, self.totals = device, {}

    def sync(self):
        if self.device == "cuda":
            torch.cuda.synchronize()
        elif self.device == "mps":
            torch.mps.synchronize()

    def __call__(self, name: str):
        timer = self

        class _Span:
            def __enter__(self):
                timer.sync()
                self.t = time.perf_counter()

            def __exit__(self, *exc):
                timer.sync()
                timer.totals[name] = (
                    timer.totals.get(name, 0.0) + time.perf_counter() - self.t
                )

        return _Span()


def grpo_step(
    policy,
    ref,
    opt,
    prompts,
    responses,
    rewards,
    cfg,
    device: str,
    timer: Timer,
    sched=None,
) -> dict:
    """One GRPO step on B*G rollouts: score old and reference log-probs once, then take
    `cfg.updates` optimizer steps, each on one minibatch slice of the rollouts."""
    pad = cfg.pad
    batch = pack(prompts, responses, pad, device)
    n, mb = len(responses), cfg.microbatch
    rew = torch.tensor(rewards, dtype=torch.float32, device=device)
    adv = group_advantages(rew, cfg.group)
    with timer("score"), torch.no_grad():
        old, ref_lp, ents = [], [], []
        policy.eval()
        for s in range(0, n, mb):
            rows = slice(s, s + mb)
            lp, ent = token_logprobs(policy, batch, rows, entropy=True)
            old.append(lp)
            ents.append(ent)
            if (
                ref is None
            ):  # LoRA: the reference is the same weights with the adapters off
                with adapters_off(policy):
                    ref_lp.append(token_logprobs(policy, batch, rows)[0])
            else:
                ref_lp.append(token_logprobs(ref, batch, rows)[0])
        old, ref_lp, ents = torch.cat(old), torch.cat(ref_lp), torch.cat(ents)
    mask = batch["response_mask"]
    stats = {
        "entropy": float((ents * mask).sum() / mask.sum()),
        "kl": 0.0,
        "clipFraction": 0.0,
        "loss": 0.0,
    }
    policy.train()
    per_update = n // cfg.updates
    with timer("train"):
        for u in range(cfg.updates):
            opt.zero_grad(set_to_none=True)
            lo, hi = u * per_update, (u + 1) * per_update
            for s in range(lo, hi, mb):
                rows = slice(s, min(s + mb, hi))
                lp, _ = token_logprobs(policy, batch, rows)
                loss, st = grpo_loss(
                    lp,
                    old[rows],
                    ref_lp[rows],
                    adv[rows],
                    mask[rows],
                    cfg.clip,
                    cfg.beta,
                )
                share = (rows.stop - rows.start) / per_update
                (loss * share).backward()
                for k in ("kl", "clipFraction"):
                    stats[k] += st[k] * share / cfg.updates
                stats["loss"] += float(loss.detach()) * share / cfg.updates
            torch.nn.utils.clip_grad_norm_(
                [p for p in policy.parameters() if p.requires_grad], cfg.max_grad_norm
            )
            opt.step()
            if sched is not None:
                sched.step()
    groups = rew.view(-1, cfg.group)
    stats["zeroVarianceGroups"] = float(
        (groups.std(1, unbiased=False) == 0).float().mean()
    )
    return stats
