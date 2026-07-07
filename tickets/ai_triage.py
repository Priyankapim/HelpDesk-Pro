import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from tickets.services.ai_service import analyze_ticket


@require_POST
def ai_triage(request):

    try:

        data = json.loads(request.body)

        subject = data.get("subject", "").strip()
        description = data.get("description", "").strip()

        if not subject or not description:

            return JsonResponse({
                "success": False,
                "error": "Subject and Description are required."
            })

        result = analyze_ticket(subject, description)

        return JsonResponse({
            "success": True,
            "result": result
        })

    except Exception as e:

        return JsonResponse({
            "success": False,
            "error": str(e)
        })