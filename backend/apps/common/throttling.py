from rest_framework.throttling import ScopedRateThrottle


class PostScopedRateThrottle(ScopedRateThrottle):
    """Apply a view's configured scope only to POST requests."""

    def allow_request(self, request, view):
        if request.method != "POST":
            return True
        return super().allow_request(request, view)
