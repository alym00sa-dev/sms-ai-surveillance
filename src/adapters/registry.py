"""Build an adapter from a config/models.json entry."""
from __future__ import annotations

from .anthropic import AnthropicAdapter
from .google import GoogleAdapter
from .openai import OpenAIAdapter
from .together import TogetherAdapter

ADAPTERS = {"anthropic": AnthropicAdapter, "openai": OpenAIAdapter, "google": GoogleAdapter, "together": TogetherAdapter}


def build_adapter(key: str, cfg: dict, native_schema: bool | None = None):
    name = cfg.get("adapter")
    if name not in ADAPTERS:
        raise ValueError(f"adapter {name!r} for model {key!r} is not implemented")
    return ADAPTERS[name](key, cfg, native_schema=native_schema)
