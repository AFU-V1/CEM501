"""
drafter.py -- Drafter component
Takes a classified email and generates a draft response using OpenAI.
"""

import logging
import os
from openai import OpenAI

logger = logging.getLogger("agent")

def draft_reply(email_data: dict) -> str:
    category = email_data["category"]
    subject = email_data["subject"]
    sender = email_data["sender"]
    body = email_data["body"]

    prompt = (
        f"You are a construction project manager's AI communication assistant.\n\n"
        f"An email was received and classified as **{category}**.\n\n"
        f"--- ORIGINAL EMAIL ---\n"
        f"From: {sender}\n"
        f"Subject: {subject}\n"
        f"Body:\n{body}\n"
        f"--- END ---\n\n"
        f"Draft a professional reply appropriate for a construction project context.\n"
        f"Guidelines:\n"
        f"- Be direct, concise, and action-oriented.\n"
        f"- For URGENT emails: acknowledge the urgency, state immediate next steps.\n"
        f"- For ACTION emails: confirm receipt, state your intended action and timeline.\n"
        f"- Use a formal but approachable tone.\n"
        f"- Keep the reply under 150 words.\n"
        f"- Do NOT include a subject line -- only the body of the reply.\n"
        f"- Do NOT add any placeholders like [Your Name].\n"
    )

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        draft = response.choices[0].message.content.strip()
        logger.info("Draft generated for: %s", subject[:60])
        return draft
    except Exception as exc:
        logger.error("LLM draft generation failed: %s", exc)
        if category == "URGENT":
            return (
                "Thank you for flagging this urgent matter. I have received your message "
                "and am reviewing it immediately. I will respond with a detailed action "
                "plan within the next two hours. Please do not hesitate to call if the "
                "situation requires immediate attention."
            )
        return (
            "Thank you for your email. I have received your message and will review "
            "the details. I will follow up with a response by end of business today."
        )
