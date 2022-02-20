class RepositoryError(Exception):
    """Base exception for all repository errors."""


class StorageAlreadyInRepositoryError(RepositoryError):
    """If the repository already contains this storage."""


class StorageDoesNotExistInRepositoryError(RepositoryError):
    """If the repository doesn't contain this storage."""


class InvalidRepositoryVersionError(RepositoryError):
    """If the wrong repository version is loaded."""


class WrongPasswordError(RepositoryError):
    """If the wrong password was passed."""
