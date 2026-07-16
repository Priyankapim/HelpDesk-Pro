from mistralai import Mistral
from django.conf import settings
import json

client = Mistral(api_key=settings.MISTRAL_API_KEY)



def analyze_ticket(subject, description):

    prompt = f"""
You are an IT HelpDesk AI.

Analyze this support ticket.

Subject:
{subject}

Description:
{description}

Return ONLY valid JSON.

Use this exact format.

{{
    "department":"",
    "category":"",
    "priority":"",
    "affected_system":"",
    "tags":[],
    "confidence":0
}}

Departments:

- IT Support
- HR Support
- Admin Support
- Finance Requests
- Asset Requests
- Access Management
- General Services

Categories:

IT Support
- Hardware Issue
- Software Issue
- Network Issue
- Email / Outlook

HR Support
- New Employee Onboarding
- Leave Policy
- Payroll Inquiry

Admin Support
- Office Supplies
- Facility Request

Finance Requests
- Invoice Processing
- Budget Approval

Asset Requests
- Laptop Request
- Software License

Access Management
- Account Creation
- Permission Request
- VPN Access

General Services
- General Inquiry

Rules:

1. Choose exactly ONE department.

2. Choose exactly ONE category.

3. Choose exactly ONE priority:
Low
Medium
High
Critical

4. affected_system MUST be exactly one of these values.
Laptop
Desktop
Printer
Windows
Office 365
Outlook
Email
Network
VPN
Authentication
Active Directory
HRMS
Payroll
Hardware
Software
Database
Website
Other

Never invent a new affected_system.

If none match, return "Other".

5. tags should contain 3-5 short keywords.

6. Return ONLY valid JSON.

Do not include explanations.

Do not use markdown.
"""

    try:
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

    except Exception as e:
        print("========== API ERROR ==========")
        print(type(e))
        print(e)
        raise

    message = response.choices[0].message

    print("\n========== FULL RESPONSE ==========\n")
    print(message)
    print("\n===================================\n")

    text = message.content

    print("\n========== CONTENT ==========\n")
    print(repr(text))
    print("\n=============================\n")

    if not text:
        raise Exception("Mistral returned an empty response.")

    # Remove markdown if present
    text = text.replace("```json", "").replace("```", "").strip()

    # Extract only JSON
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1:
        text = text[start:end + 1]

    print("\n========== CLEAN JSON ==========\n")
    print(text)
    print("\n================================\n")

    return json.loads(text)


def ai_assistant_reply(history):
    """
    history: list of {"role": "user"|"assistant", "content": "..."}
    Returns the assistant's plain-text reply using the same Mistral client
    already configured for ticket triage.
    """

    system_prompt = {
        "role": "system",
        "content": (
            "You are the AI Assistant inside ServiceDesk Pro, an IT helpdesk "
            "portal. You help employees troubleshoot common IT issues, explain "
            "how to raise support tickets, describe SLA timelines, and answer "
            "general IT support questions. Keep answers short, practical, and "
            "friendly. If the issue sounds like it needs a human agent, suggest "
            "the user raise a ticket using the 'Raise Ticket' button. "
            "Do not invent company-specific policies you don't know - if unsure, "
            "say so and suggest raising a ticket instead."
        )
    }

    messages = [system_prompt] + history

    response = client.chat.complete(
        model="mistral-small-latest",
        messages=messages
    )

    message = response.choices[0].message
    text = message.content

    if not text:
        raise Exception("Mistral returned an empty response.")

    return text.strip()