"""Generate construction-focused draft responses with history-aware context."""

import logging
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logger = logging.getLogger("agent")

def draft_reply(email_data: dict) -> str:
    category = email_data["category"]
    message_type = email_data.get("message_type", "GENERAL")
    subject = email_data["subject"]
    sender = email_data["sender"]
    body = email_data["body"]
    history_context = email_data.get("history_context", "No prior history available.")
    channel = email_data.get("channel", "email")

    prompt = (
        f"You are a construction project manager's AI communication assistant.\n\n"
        f"A {channel} message was received and classified as workflow category "
        f"'{category}' and construction type '{message_type}'.\n\n"
        f"--- ORIGINAL EMAIL ---\n"
        f"From: {sender}\n"
        f"Subject: {subject}\n"
        f"Body:\n{body}\n"
        f"--- END ---\n\n"
        f"--- RECENT HISTORY ---\n{history_context}\n--- END HISTORY ---\n\n"
        f"Draft a professional reply appropriate for a construction project context.\n"
        f"Guidelines:\n"
        f"- Be direct, concise, and action-oriented.\n"
        f"- For URGENT items: acknowledge urgency and state immediate next steps.\n"
        f"- For ACTION items: confirm receipt, state intended action and timeline.\n"
        f"- Use realistic construction communication language for RFIs, approvals, delays, safety, site issues, and procurement.\n"
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
        if message_type == "SAFETY" or category == "URGENT":
            return (
                "Thank you for flagging this urgent matter. I have received your message "
                "and am reviewing it immediately. I will respond with a detailed action "
                "plan within the next two hours. Please do not hesitate to call if the "
                "situation requires immediate attention."
            )
        if message_type == "RFI":
            return (
                "Thank you for the RFI. I have logged the request and will review the "
                "drawing and specification references before responding. You can expect "
                "a coordinated reply by the next business update."
            )
        if message_type == "APPROVAL":
            return (
                "Thank you for sending this item for approval. I have received it and "
                "started the review with the relevant project documents. I will revert "
                "with comments or approval status as soon as the review is complete."
            )
        return (
            "Thank you for your email. I have received your message and will review "
            "the details. I will follow up with a response by end of business today."
        )
