class AppError(Exception):
    """Base application error."""


class GenerationNotConfiguredError(AppError):
    """Raised when generation is requested before the LLM provider is configured."""
