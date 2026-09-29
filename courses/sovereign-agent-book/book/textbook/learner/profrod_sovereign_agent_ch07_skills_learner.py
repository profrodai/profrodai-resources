# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 7's skill record and its bounded read. Staging and activation build on these."""

import os
import stat
import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class Skill(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")
    version: str = Field(pattern=r"^[a-zA-Z0-9._-]{1,64}$")
    instructions: str = Field(min_length=1, max_length=8192)
    requires: list[str] = Field(default_factory=list, max_length=16)


def read_skill(path: Path) -> bytes:
    """Read one bounded regular file; POSIX flags refuse symlinks and FIFO waits."""
    if path.is_symlink():
        raise ValueError("bounded regular local skill file required")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as stream:
            observed = os.fstat(stream.fileno())
            if not stat.S_ISREG(observed.st_mode) or observed.st_size > 16_384:
                raise ValueError("bounded regular local skill file required")
            raw = stream.read(16_385)
    except OSError as error:
        raise ValueError("readable regular local skill file required") from error
    if len(raw) > 16_384:
        raise ValueError("skill changed beyond byte limit")
    return raw


def load_skill(path: Path) -> Skill:
    """A skill file, read within its bound and validated strictly."""
    return Skill.model_validate(tomllib.loads(read_skill(path).decode()))
