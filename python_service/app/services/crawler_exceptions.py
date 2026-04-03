"""Crawler-specific exceptions for Bilibili access."""


class CommentFetchException(Exception):
    """Base exception for comment fetching failures."""


class BilibiliRiskControlException(CommentFetchException):
    """Raised when Bilibili returns explicit anti-bot / risk-control responses."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code

