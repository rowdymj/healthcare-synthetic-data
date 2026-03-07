"""Adapters — data abstraction layer for HealthcarePlatform."""

from adapters.sandbox_adapter import SandboxAdapter
from adapters.interface_validator import validate_adapter, REQUIRED_METHODS

__all__ = ["SandboxAdapter", "validate_adapter", "REQUIRED_METHODS"]
