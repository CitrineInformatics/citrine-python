from typing import Optional


class AsynchronousObject:
    """Abstract class for objects that are asynchronously populated."""

    _in_progress_statuses = []  # list of statuses that indicate 'in progress'
    _succeeded_statuses = []  # list of statuses that indicate 'succeeded'
    _failed_statuses = []  # list of statuses that indicate 'failed'

    def _fetch_status(self) -> Optional[str]:
        """Fetch the status of the resource.

        This is is the `status` attribute by default, but can be overridden if the status
        is encoded differently and/or we want to pull an update from the backend.
        """
        return self.status

    def in_progress(self) -> bool:
        """Whether the backend process is in progress."""
        updated_status = self._fetch_status()
        return any(updated_status == s for s in self._in_progress_statuses)

    def succeeded(self) -> bool:
        """Whether the backend process has completed successfully."""
        updated_status = self._fetch_status()
        return any(updated_status == s for s in self._succeeded_statuses)

    def failed(self) -> bool:
        """Whether the backend process has completed unsuccessfully."""
        updated_status = self._fetch_status()
        return any(updated_status == s for s in self._failed_statuses)
