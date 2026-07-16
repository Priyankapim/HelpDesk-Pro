from mistralai import Mistral
from django.conf import settings

client = Mistral(api_key=settings.MISTRAL_API_KEY)


def generate_summary(title, content):

    prompt = f"""
You are a Knowledge Base editor for an IT HelpDesk system.

Write a short, clear summary (2-3 sentences, maximum 40 words) for the
article below. The summary will be shown on article cards and at the top
of the article page.

Title:
{title}

Content:
{content}

Return ONLY the summary text.
Do not use markdown.
Do not include quotes.
Do not include a heading.
"""

    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    message = response.choices[0].message
    text = (message.content or "").strip()

    text = text.strip('"').strip()

    if not text:
        raise Exception("Mistral returned an empty summary.")

    return text
