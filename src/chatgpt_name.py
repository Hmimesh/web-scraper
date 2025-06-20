import os
import logging

# Attempt to import openai when available
try:
    import openai  # type: ignore
except Exception:  # pragma: no cover - openai may not be installed
    openai = None


def guess_hebrew_name(text: str) -> str | None:
    """Return the best Hebrew personal name for the given text using ChatGPT.

    The OpenAI API key is read from the ``OPENAI_API_KEY`` environment
    variable. If the key or the ``openai`` package is missing, ``None`` is
    returned.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or not text or openai is None:
        return None

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Return the best Hebrew personal name for the provided text.",
                },
                {"role": "user", "content": text},
            ],
            max_tokens=4,
            temperature=0,
        )
    except Exception:
        logging.exception("OpenAI request failed")
        return None

    try:
        if isinstance(response, dict):
            result = response["choices"][0]["message"]["content"].strip()
        else:
            result = response.choices[0].message.content.strip()
    except Exception:
        return None

    return result or None


def guess_hebrew_department(
    text: str | None = None, url: str | None = None
) -> str | None:
    """Return the best Hebrew department name for the given text or URL using ChatGPT.

    The OpenAI API key is read from the ``OPENAI_API_KEY`` environment
    variable. If the key or the ``openai`` package is missing, ``None`` is
    returned.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or openai is None:
        return None

    prompt_parts = []
    if text:
        prompt_parts.append(text)
    if url:
        prompt_parts.append(f"URL: {url}")

    if not prompt_parts:
        return None

    prompt = "\n".join(prompt_parts)

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Return the best Hebrew department name for the provided text or URL."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=6,
            temperature=0,
        )
    except Exception:
        logging.exception("OpenAI request failed")
        return None

    try:
        if isinstance(response, dict):
            result = response["choices"][0]["message"]["content"].strip()
        else:
            result = response.choices[0].message.content.strip()
    except Exception:
        return None

    return result or None
