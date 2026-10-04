from core.current_user import acting_as


class CurrentUserMiddleware:
    """
    Exposes request.user to the audit layer for the whole request.
    Must run after AuthenticationMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        with acting_as(request.user):
            return self.get_response(request)
