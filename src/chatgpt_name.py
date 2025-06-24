import os
import openai
import logging


def guess_hebrew_name(text: str) -> str | None:
    """Return the best Hebrew personal name for the given text using ChatGPT."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or not text:
        return None

    openai.api_key = api_key

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Return only the best Hebrew personal name for the provided text. Do not explain.",
                },
                {"role": "user", "content": text},
            ],
            max_tokens=5,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.exception("OpenAI request failed")
        return None


def guess_hebrew_department(text: str | None = None, url: str | None = None) -> str | None:
    """Return the best Hebrew department name for the given text or URL using ChatGPT."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    openai.api_key = api_key

    prompt_parts = []
    if text:
        prompt_parts.append(text)
    if url:
        prompt_parts.append(f"URL: {url}")

    if not prompt_parts:
        return None

    prompt = "\n".join(prompt_parts)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Return only the best matching Hebrew department name for the given text or URL. Be concise and do not explain.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=8,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.exception("OpenAI request failed")
        return None
