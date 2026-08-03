from mistralai import Mistral
from django.conf import settings
import json

client = Mistral(api_key=settings.MISTRAL_API_KEY)



def _build_department_category_block():
    """
    Pull real department/category names from the DB so the AI
    always suggests values that actually exist in the dropdowns.
    Prevents drift like 'Access Management' vs 'Access Managements'.
    """
    from departments.models import Department

    depts = Department.objects.filter(is_active=True).prefetch_related("categories")

    dept_lines = [f"- {d.name}" for d in depts]

    category_blocks = []
    for d in depts:
        cats = d.categories.filter(is_active=True)
        if cats:
            block = d.name + "\n" + "\n".join(f"- {c.name}" for c in cats)
            category_blocks.append(block)

    return "\n".join(dept_lines), "\n\n".join(category_blocks)


def analyze_ticket(subject, description):

    dept_block, category_block = _build_department_category_block()

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

Departments (use the EXACT spelling shown):

{dept_block}

Categories (use the EXACT spelling shown):

{category_block}

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


def ai_assistant_reply(history, role="EMPLOYEE"):
    """
    history: list of {"role": "user"|"assistant", "content": "..."}
    role: the requesting user's role, used to pick the right persona.
    Returns the assistant's plain-text reply using the same Mistral client
    already configured for ticket triage.
    """

    if role == "SUPER_ADMIN":
        prompt_text = (
            "You are the AI Assistant inside ServiceDesk Pro, used here by "
            "the platform's Super Admin (not a tenant employee). "
            "\n\n"
            "IMPORTANT — only these features actually exist in this app. "
            "Do not invent buttons, fields, or workflows beyond this list:\n"
            "- A Support Request has only these fields: Subject, Description, "
            "Priority (Low/Medium/High/Critical), Status (Open/In Progress/"
            "Pending User/Resolved/Closed), and which Tenant raised it.\n"
            "- There is no Category field, no Assignee field, no SLA timer, "
            "no Internal Notes, no Templates feature, no satisfaction survey, "
            "and no Escalate button on Support Requests.\n"
            "- Replying happens as a simple message thread on the request — "
            "each reply is just marked as either a staff reply or a tenant "
            "reply, nothing more structured than that.\n"
            "- Other real Super Admin pages: Tenant Management (create/view "
            "tenants, plan, active status), Platform Audit Log (tenant "
            "lifecycle events).\n"
            "\n"
            "You help with: drafting a reply message for a Support Request, "
            "explaining what a Priority/Status value means, and general "
            "guidance on using the pages above. If asked about something "
            "not in this list, say plainly that ServiceDesk Pro doesn't have "
            "that feature yet, instead of describing how to use it. Keep "
            "answers short and practical."
        )
    else:
        prompt_text = (
            "You are the AI Assistant inside ServiceDesk Pro, an IT helpdesk "
            "portal. You help employees troubleshoot common IT issues, explain "
            "how to raise support tickets, describe SLA timelines, and answer "
            "general IT support questions. Keep answers short, practical, and "
            "friendly. If the issue sounds like it needs a human agent, suggest "
            "the user raise a ticket using the 'Raise Ticket' button. "
            "Do not invent company-specific policies you don't know - if unsure, "
            "say so and suggest raising a ticket instead."
        )

    system_prompt = {
        "role": "system",
        "content": prompt_text
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