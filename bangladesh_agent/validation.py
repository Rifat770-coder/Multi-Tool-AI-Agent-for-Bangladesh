"""Shared request bounds for CLI, UI and tools."""
MAX_QUESTION_LENGTH = 2000


def validate_question(question):
    if not isinstance(question, str) or not question.strip():
        raise ValueError('Please enter a question.')
    if len(question) > MAX_QUESTION_LENGTH:
        raise ValueError(f'Questions must be at most {MAX_QUESTION_LENGTH} characters.')
    return question.strip()
