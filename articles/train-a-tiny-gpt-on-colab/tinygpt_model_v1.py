# Prof Rod | Train a Tiny GPT on Colab
# Article: https://profrod.ai/articles/train-a-tiny-gpt-on-colab
# Original source and updates: https://github.com/profrodai/profrodai-resources

"""A small GPT in plain PyTorch: token and position embeddings, pre-norm blocks of causal
self-attention and an MLP, a final LayerNorm and an output head tied to the token embedding.

Attention is written out by hand (scores, mask, softmax, weighted sum) rather than calling
`scaled_dot_product_attention`, so every line a bug can live in is visible.

Planted bugs, each a one-line change selected by name (`BUGS`):
- `no_causal_mask`: the mask line is skipped, so each position attends to the future.
- `softmax_wrong_dim`: attention weights are normalized over the queries (dim -2), not the keys.
- `no_zero_grad`: lives in the training loop (tinygpt_run_v1.py): gradients are never cleared.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F

BUGS = ("none", "no_causal_mask", "softmax_wrong_dim", "no_zero_grad")


@dataclass
class Config:
    vocab_size: int = 4096
    block_size: int = 256
    n_layer: int = 6
    n_head: int = 6
    n_embd: int = 384
    bug: str = "none"

    def as_dict(self) -> dict:
        return asdict(self)


class CausalSelfAttention(nn.Module):
    def __init__(self, cfg: Config):
        super().__init__()
        assert cfg.n_embd % cfg.n_head == 0
        self.n_head, self.bug = cfg.n_head, cfg.bug
        self.qkv = nn.Linear(cfg.n_embd, 3 * cfg.n_embd)
        self.proj = nn.Linear(cfg.n_embd, cfg.n_embd)
        mask = torch.tril(torch.ones(cfg.block_size, cfg.block_size, dtype=torch.bool))
        self.register_buffer("mask", mask, persistent=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, T, C = x.shape
        q, k, v = self.qkv(x).split(C, dim=2)
        q, k, v = (t.view(B, T, self.n_head, C // self.n_head).transpose(1, 2) for t in (q, k, v))  # (B, h, T, d)
        att = (q @ k.transpose(-2, -1)) / math.sqrt(k.size(-1))  # (B, h, T queries, T keys)
        if self.bug != "no_causal_mask":
            att = att.masked_fill(~self.mask[:T, :T], float("-inf"))
        att = F.softmax(att, dim=-2 if self.bug == "softmax_wrong_dim" else -1)
        y = (att @ v).transpose(1, 2).contiguous().view(B, T, C)
        return self.proj(y)


class MLP(nn.Module):
    def __init__(self, cfg: Config):
        super().__init__()
        self.fc = nn.Linear(cfg.n_embd, 4 * cfg.n_embd)
        self.proj = nn.Linear(4 * cfg.n_embd, cfg.n_embd)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.proj(F.gelu(self.fc(x)))


class Block(nn.Module):
    def __init__(self, cfg: Config):
        super().__init__()
        self.ln1, self.attn = nn.LayerNorm(cfg.n_embd), CausalSelfAttention(cfg)
        self.ln2, self.mlp = nn.LayerNorm(cfg.n_embd), MLP(cfg)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(self.ln1(x))
        return x + self.mlp(self.ln2(x))


class GPT(nn.Module):
    def __init__(self, cfg: Config):
        super().__init__()
        self.cfg = cfg
        self.wte = nn.Embedding(cfg.vocab_size, cfg.n_embd)
        self.wpe = nn.Embedding(cfg.block_size, cfg.n_embd)
        self.blocks = nn.ModuleList(Block(cfg) for _ in range(cfg.n_layer))
        self.ln_f = nn.LayerNorm(cfg.n_embd)
        self.head = nn.Linear(cfg.n_embd, cfg.vocab_size, bias=False)
        self.head.weight = self.wte.weight  # tied, as in GPT-2
        self.apply(self._init)
        for name, p in self.named_parameters():  # GPT-2: scale residual projections by 1/sqrt(2 * layers)
            if name.endswith("proj.weight"):
                nn.init.normal_(p, mean=0.0, std=0.02 / math.sqrt(2 * cfg.n_layer))

    @staticmethod
    def _init(m: nn.Module) -> None:
        if isinstance(m, (nn.Linear, nn.Embedding)):
            nn.init.normal_(m.weight, mean=0.0, std=0.02)
        if isinstance(m, nn.Linear) and m.bias is not None:
            nn.init.zeros_(m.bias)

    def num_params(self) -> int:
        """Every parameter counted once (the tied head shares the token embedding)."""
        return sum(p.numel() for p in self.parameters())

    def forward(self, idx: torch.Tensor, targets: torch.Tensor | None = None):
        B, T = idx.shape
        pos = torch.arange(T, device=idx.device)
        x = self.wte(idx) + self.wpe(pos)
        for block in self.blocks:
            x = block(x)
        logits = self.head(self.ln_f(x))
        if targets is None:
            return logits, None
        return logits, F.cross_entropy(logits.reshape(-1, logits.size(-1)), targets.reshape(-1))


def flops_per_token(cfg: Config) -> float:
    """Training FLOPs per token: 6 per matmul weight (forward 2, backward 4), plus attention scores
    and the weighted sum (2 matmuls of T x d per position, per layer), also times 3 for training.
    Embedding lookups are not matmuls and are left out; the tied head is counted once."""
    d, L, T, V = cfg.n_embd, cfg.n_layer, cfg.block_size, cfg.vocab_size
    matmul_weights = L * 12 * d * d + V * d
    attention = L * 2 * T * d  # q.k for T keys and att.v over T values, multiply-adds per token
    return 6 * matmul_weights + 6 * attention


def optimizer_groups(model: GPT, weight_decay: float) -> list[dict]:
    """Decay matrices (dim >= 2, including the tied embedding); never biases or LayerNorm gains."""
    decay = [p for p in model.parameters() if p.dim() >= 2]
    no_decay = [p for p in model.parameters() if p.dim() < 2]
    return [{"params": decay, "weight_decay": weight_decay}, {"params": no_decay, "weight_decay": 0.0}]
