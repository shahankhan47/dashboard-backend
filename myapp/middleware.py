import os
from django.http import JsonResponse

API_KEY = os.getenv('API_KEY')

class SimpleAPIKeyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        api_key = request.headers.get("Authorization")

        if api_key != API_KEY:
            return JsonResponse({"error": "Unauthorized"}, status=401)

        return self.get_response(request)
