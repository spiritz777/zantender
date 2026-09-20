"""User-safe document processing errors."""


class DocumentProcessingError(RuntimeError):
    """Base error for an unprocessable user document."""


class UnsupportedDocumentError(DocumentProcessingError):
    """Raised when a document format is not supported."""


class EmptyDocumentError(DocumentProcessingError):
    """Raised when no readable text is found in a document."""


class DocumentTooLargeError(DocumentProcessingError):
    """Raised when an uploaded file exceeds the configured size limit."""
