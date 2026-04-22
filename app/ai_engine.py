from openai import OpenAI

CATEGORIES = [
    "Food & Dining",
    "Transportation",
    "Entertainment",
    "Utilities",
    "Shopping",
    "Health & Medical",
    "Travel",
    "Education",
    "Personal Care",
    "Subscriptions",
    "Housing",
    "Other",
]

_SYSTEM_PROMPT = (
    "You are a financial expense categorizer. Given a description and amount, "
    "return ONLY a single category string — no explanation, no punctuation, no extra text whatsoever.\n\n"
    "Choose the single best-matching category from this list:\n"
    + "\n".join(f"- {c}" for c in CATEGORIES)
    + "\n\nIf the expense does not clearly fit any category, return: Other"
)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()  # reads OPENAI_API_KEY from environment
    return _client


def categorize_expense(description: str, amount: float) -> str:
    try:
        response = _get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": f"Description: {description}\nAmount: ${amount:.2f}"},
            ],
            max_tokens=10,
            temperature=0,
        )
        category = response.choices[0].message.content.strip()
        return category if category else "Uncategorized"
    except Exception as e:
        print(f"OpenAI Error: {e}")
        return "Uncategorized"
