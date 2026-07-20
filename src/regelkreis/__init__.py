"""Public, stateless convergence protocol evaluator."""

from .core import ContractValidationError, evaluate

__all__ = ["ContractValidationError", "evaluate"]
__version__ = "1.1.0"
