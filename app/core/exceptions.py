class ResumeAgentException(Exception):
    """Base exception class for all errors in the Resume Screening Agent application."""
    def __init__(self, message: str = "An error occurred within the Resume Screening Agent"):
        self.message = message
        super().__init__(self.message)


class ValidationException(ResumeAgentException):
    """Raised when request payload or data schema validation fails."""
    def __init__(self, message: str = "Validation failed for input data"):
        super().__init__(message)


class ParsingException(ResumeAgentException):
    """Raised when there is an error reading or extracting text from resumes or JDs."""
    def __init__(self, message: str = "Failed to parse resume document content"):
        super().__init__(message)


class LLMException(ResumeAgentException):
    """Raised when an external Large Language Model service call fails."""
    def __init__(self, message: str = "External LLM service call failed"):
        super().__init__(message)


class ScoringException(ResumeAgentException):
    """Raised when scoring algorithm or metrics calculation fails."""
    def __init__(self, message: str = "Failure during matching or scoring process"):
        super().__init__(message)


class ExportException(ResumeAgentException):
    """Raised when writing analysis results to output reports (CSV, JSON, PDF) fails."""
    def __init__(self, message: str = "Failed to export report records"):
        super().__init__(message)
