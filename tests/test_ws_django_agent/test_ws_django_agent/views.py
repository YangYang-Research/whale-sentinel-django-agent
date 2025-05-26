# views.py
from whale_sentinel_django_agent import WhaleSentinelDjangoAgent
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json


ws_agent = WhaleSentinelDjangoAgent()

@csrf_exempt
@ws_agent.whale_sentinel_agent_protection()
def search(request):
    """
    Search endpoint for Django
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    search_query = data.get("query")
    if not search_query:
        return JsonResponse({"error": "Query parameter is required"}, status=400)

    response = {
        "query": search_query,
        "results": [
            {"id": 1, "name": "Result 1"},
            {"id": 2, "name": "Result 2"},
            {"id": 3, "name": "Result 3"},
        ],
    }
    return JsonResponse(response)

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(ws_agent.whale_sentinel_agent_protection(), name='dispatch')
class SearchView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            search_query = data.get("query")
            if not search_query:
                return JsonResponse({"error": "Query parameter is required"}, status=400)

            response = {
                "query": search_query,
                "results": [
                    {"id": 1, "name": "Result 1"},
                    {"id": 2, "name": "Result 2"},
                    {"id": 3, "name": "Result 3"},
                ]
            }
            return JsonResponse(response)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)