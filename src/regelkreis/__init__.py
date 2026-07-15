"""Public, stateless convergence protocol evaluator."""

from .core import ContractValidationError, evaluate

__all__ = ["ContractValidationError", "evaluate"]
__version__ = "0.1.0"
