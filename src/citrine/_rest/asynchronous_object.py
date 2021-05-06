from abc import abstractmethod


class AsynchronousObject:
    """Abstract class for objects that are asynchronously populated."""

    @abstractmethod
    def in_progress(self) -> bool:
        """Whether the backend process is in progress."""

    @abstractmethod
    def succeeded(self) -> bool:
        """Whether the backend process has completed successfully."""

    def failed(self) -> bool:
        """Whether the backend process has completed unsuccessfully."""
