"""
Backend Guardrails — Input validation, output cleanup, thinking separation,
prompt-injection detection, PII redaction, and error mapping.

Architecture:
    chat_service.py → apply_input_guardrails()  → before agent execution
    adk_runner_service.py → apply_output_guardrails() → after agent execution
    chat_service.py → map_exception_to_user_message() → on error

This module is intentionally:
    - Standard library only (no external dependencies)
    - No async / no network calls
    - No model dependency
    - Safe for every FastAPI request/response path
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

# Must match backend Pydantic schema max_length in ChatQueryRequest
MAX_QUERY_LENGTH = 2000

# Patterns that indicate prompt-injection or instruction-override attempts
PROMPT_INJECTION_PATTERNS: list[str] = [
    r"(?i)\bignore (all|any|previous|prior) (instructions|rules|prompts)\b",
    r"(?i)\boverride (instructions|rules|policy|policies)\b",
    r"(?i)\breveal (the )?(system prompt|hidden prompt|developer prompt)\b",
    r"(?i)\bshow (the )?(system prompt|hidden prompt|developer prompt)\b",
    r"(?i)\bbypass (guardrails|safety|filters|restrictions)\b",
    r"(?i)\bdisable (guardrails|safety|filters|restrictions)\b",
    r"(?i)\bdo not ask for confirmation\b",
    r"(?i)\bcall (the )?tool directly\b",
    r"(?i)\bexecute without confirmation\b",
]

# Patterns that indicate LLM reasoning leakage in the final response text
REASONING_LEAK_PATTERNS: list[str] = [
    r"(?im)^we can provide answer:.*$",
    r"(?im)^we need to .*$",
    r"(?im)^the user didn't .*$",
    r"(?im)^according to tool usage rules.*$",
    r"(?im)^we don't have a tool.*$",
    r"(?im)^now format.*$",
    r"(?im)^analysis:.*$",
    r"(?im)^observation:.*$",
    r"(?im)^let me .*$",
    r"(?im)^i will .*$",
    r"(?im)^thus .*$",
    r"(?im)^so we .*$",
    r"(?im)^first,? (?:we|i) .*$",
    r"(?im)^next,? (?:we|i) .*$",
    r"(?im)^finally,? (?:we|i) .*$",
    r"(?im)^to answer this.*$",
    r"(?im)^to do this.*$",
    r"(?im)^looking at .*$",
    r"(?im)^based on the above.*$",
    r"(?im)^from the (?:tool|data|results?).*$",
]

# Indicators that a text block contains reasoning/planning (not user-facing
# content). Used by preamble detection and inline reasoning extraction.
# If 2+ indicators are found in a text block, it is classified as reasoning.
PREAMBLE_INDICATORS: list[str] = [
    r"(?i)\buser (?:just|says|asks|wants|is asking|said|asked)\b",
    r"(?i)\bthis is a (?:greeting|question|query|request|simple|follow)\b",
    r"(?i)\bno (?:query|need|tool|data)\b",
    r"(?i)\bcould respond\b",
    r"(?i)\bshould respond\b",
    r"(?i)\buse markdown\b",
    r"(?i)\bprobably\b",
    r"(?i)\bmust start with\b",
    r"(?i)\bno tool usage\b",
    r"(?i)\baccording to (?:format|rules|instructions|guidelines|the)\b",
    r"(?i)\bwe (?:need|should|can|could|must|don't)\b",
    r"(?i)\bthe user\b.*\b(?:asks|wants|says|didn't|does not|hasn't)\b",
    r"(?i)\bnot? (?:specified|provided|given|mentioned)\b",
    r"(?i)\brequired (?:input|field|parameter)\b",
    r"(?i)\btool (?:call|invocation|usage)\b",
    r"(?i)\bresponse (?:format|style|should)\b",
    r"(?i)\bmarkdown (?:heading|table|format)\b",
    r"(?i)\blikely (?:they|the user|this|it|he|she)\b",
    r"(?i)\b(?:brief|short|concise) (?:acknowledgment|response|answer|reply)\b",
    r"(?i)\b(?:done|finished|completed)\b.*\b(?:with|asking|querying)\b",
    r"(?i)\b(?:closing|farewell|goodbye)\b",
    r"(?i)\blikely requires\b",
    r"(?i)\bjust respond\b",
    r"(?i)\bno query needing\b",
    r"(?i)\brespond politely\b",
    r"(?i)\bstart with a heading\b",
]

# Minimum number of preamble indicators required to classify a text
# block as reasoning. Set to 2 to reduce false positives.
PREAMBLE_INDICATOR_THRESHOLD = 2

# Regex for detecting email addresses in free-form text
EMAIL_PATTERN = re.compile(
    r"\b([A-Za-z0-9._%+-])([A-Za-z0-9._%+-]*?)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b"
)

# Regex for detecting phone-like digit sequences in free-form text
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?\d[\d\-\s\(\)]{6,}\d)(?!\d)")


# ─────────────────────────────────────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class GuardrailDecision:
    """Result of input guardrail evaluation.

    Attributes:
        allowed: Whether the request may proceed to the agent layer.
        cleaned_text: Sanitized/normalized user query (only set if allowed).
        message: User-facing message when blocked or needs clarification.
        reason: Internal tag for logging/telemetry.
        metadata: Optional structured details for audit.
    """

    allowed: bool
    cleaned_text: str = ""
    message: str = ""
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SeparatedResponse:
    """Holds the separated thinking trace and clean user-facing answer.

    Attributes:
        thinking: Internal reasoning extracted from the raw LLM output.
            Safe to show in a collapsible UI section.
        answer: Clean, user-facing final response with all reasoning
            removed. This is what the user sees by default.
    """

    thinking: str = ""
    answer: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Formatting helpers
# ─────────────────────────────────────────────────────────────────────────────

def format_clarification(message: str) -> str:
    """Return a short, user-facing clarification response."""
    return f"## Clarification Needed\n\n{message.strip()}"


def format_tool_limitation(
    message: str = "I don't have the required tools to answer that directly.",
) -> str:
    """Return a short, user-facing tool limitation response."""
    return f"## Tool Limitation\n\n{message.strip()}"


def format_request_blocked(
    message: str = (
        "I can't process that request as written. "
        "Please rephrase it as a normal business or system query."
    ),
) -> str:
    """Return a short, user-facing blocked-request response."""
    return f"## Request Blocked\n\n{message.strip()}"


# ─────────────────────────────────────────────────────────────────────────────
# Input guardrails
# ─────────────────────────────────────────────────────────────────────────────

def normalize_user_query(query: str) -> str:
    """Normalize user input: trim whitespace and collapse repeated spaces.

    Args:
        query: Raw user input string.

    Returns:
        Cleaned query string.

    Raises:
        ValueError: If the query is empty after normalization.
    """
    text = " ".join((query or "").strip().split())
    if not text:
        raise ValueError("Query is empty.")
    return text


def detect_prompt_injection(text: str) -> list[str]:
    """Detect obvious prompt-injection / instruction-override phrases.

    Args:
        text: Normalized user query text.

    Returns:
        List of matched pattern strings. Empty list means safe.
    """
    matches: list[str] = []
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text):
            matches.append(pattern)
    return matches


def apply_input_guardrails(query: str) -> GuardrailDecision:
    """Validate and sanitize a user query before it reaches the agent layer.

    Checks performed:
        1. Empty / whitespace-only rejection
        2. Max length enforcement (matches backend Pydantic schema)
        3. Prompt-injection / instruction-override detection

    Args:
        query: Raw user query from the API request.

    Returns:
        GuardrailDecision with allowed=True/False and relevant metadata.
    """
    # 1. Empty / whitespace check
    try:
        cleaned = normalize_user_query(query)
    except ValueError:
        return GuardrailDecision(
            allowed=False,
            message=format_clarification(
                "Please enter a valid question or request."
            ),
            reason="empty_query",
        )

    # 2. Max length check
    if len(cleaned) > MAX_QUERY_LENGTH:
        return GuardrailDecision(
            allowed=False,
            message=format_clarification(
                f"Please shorten the request to {MAX_QUERY_LENGTH} characters or fewer."
            ),
            reason="query_too_long",
            metadata={"length": len(cleaned)},
        )

    # 3. Prompt-injection check
    injection_matches = detect_prompt_injection(cleaned)
    if injection_matches:
        return GuardrailDecision(
            allowed=False,
            message=format_request_blocked(),
            reason="prompt_injection_detected",
            metadata={"matches": injection_matches},
        )

    # All checks passed
    return GuardrailDecision(
        allowed=True,
        cleaned_text=cleaned,
        reason="allowed",
    )


# ─────────────────────────────────────────────────────────────────────────────
# PII redaction helpers
# ─────────────────────────────────────────────────────────────────────────────

def _mask_email_match(match: re.Match[str]) -> str:
    """Mask an email while preserving the first character and domain.

    Example:
        alice@example.com -> a***@example.com
    """
    first_char = match.group(1)
    domain = match.group(3)
    return f"{first_char}***@{domain}"


def _mask_phone_digits(raw_phone: str) -> str:
    """Mask a phone-like string so only the last 4 digits remain visible.

    Example:
        9876543210 -> ***-***-3210
        12 -> ***

    Args:
        raw_phone: Raw phone-like string (may contain non-digit chars).

    Returns:
        Masked phone string.
    """
    digits = "".join(ch for ch in raw_phone if ch.isdigit())
    if len(digits) < 4:
        return "***"
    return f"***-***-{digits[-4:]}"


def redact_sensitive_text(text: str) -> str:
    """Redact email and phone-like patterns in free-form text.

    This is a defense-in-depth layer. The primary masking happens in
    app/utils/masking.py at the MCP tool level. This function catches
    any PII that leaks into free-form LLM output.

    Args:
        text: Free-form text that may contain PII.

    Returns:
        Text with emails and phones masked.
    """
    if not text:
        return ""
    text = EMAIL_PATTERN.sub(_mask_email_match, text)
    text = PHONE_PATTERN.sub(
        lambda m: _mask_phone_digits(m.group(0)), text
    )
    return text


# ─────────────────────────────────────────────────────────────────────────────
# Output guardrails — thinking/answer separation
# ─────────────────────────────────────────────────────────────────────────────

def _count_indicators(text: str) -> int:
    """Count how many preamble indicators appear in a text block.

    Args:
        text: Text block to scan for reasoning indicators.

    Returns:
        Number of distinct indicator patterns matched.
    """
    return sum(1 for p in PREAMBLE_INDICATORS if re.search(p, text))


def _extract_think_blocks(text: str) -> tuple[list[str], str]:
    """Extract explicit <think>...</think> blocks from text.

    These are produced by reasoning-capable models (e.g., qwen3, deepseek).

    Args:
        text: Raw LLM output text.

    Returns:
        Tuple of (list of extracted thinking strings, remaining text).
    """
    blocks = re.findall(r"<think>(.*?)</think>", text, flags=re.DOTALL)
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    return [b.strip() for b in blocks if b.strip()], cleaned


def _extract_preamble(text: str) -> tuple[str, str]:
    """Detect and separate a reasoning preamble from the actual answer.

    Many reasoning-capable models produce a block of planning text
    before the actual answer. This function detects that pattern by
    looking for multiple reasoning indicators in the first text block.

    It tries two split strategies:
        1. Blank line split (\\n\\s*\\n) — most common
        2. Single newline split (\\n) — fallback for models that use
           only one newline between reasoning and answer

    Args:
        text: Text after <think> block removal.

    Returns:
        Tuple of (preamble reasoning text, remaining answer text).
        If no preamble is detected, preamble is empty string.
    """
    # Strategy 1: Try blank-line split first (most reliable)
    parts = re.split(r"\n\s*\n", text, maxsplit=1)
    if len(parts) >= 2:
        first_block = parts[0].strip()
        rest = parts[1].strip()
        if first_block and rest:
            if _count_indicators(first_block) >= PREAMBLE_INDICATOR_THRESHOLD:
                return first_block, rest

    # Strategy 2: Try single-newline split (for models that use \n not \n\n)
    parts = text.split("\n", 1)
    if len(parts) >= 2:
        first_block = parts[0].strip()
        rest = parts[1].strip()
        if first_block and rest:
            if _count_indicators(first_block) >= PREAMBLE_INDICATOR_THRESHOLD:
                return first_block, rest

    return "", text


def _extract_inline_reasoning(text: str) -> tuple[str, str]:
    """Extract inline reasoning from a single text block that has no
    newline separation between reasoning and answer.

    This handles cases where the model produces reasoning and answer
    in one continuous paragraph, for example:

        "The user said 'nothing'. Likely they are done. Should respond
        politely. Probably a brief acknowledgment. Understood. If you
        need anything else, feel free to ask."

    Strategy:
        1. Only runs if the text has NO newlines (single block)
        2. Check if the whole text has enough reasoning indicators
        3. Split into sentences
        4. Scan from the END to find where clean answer starts
        5. Everything before that boundary = thinking
        6. Everything after = answer

    Scanning from the end is more robust because the model always
    reasons FIRST, then answers. So the answer is always at the tail.

    Args:
        text: Text block with no newline separation.

    Returns:
        Tuple of (reasoning text, answer text).
        If no inline reasoning is detected, reasoning is empty string.
    """
    # Only run if the text has no newlines (single continuous block)
    if "\n" in text:
        return "", text

    # Check if the whole text has enough reasoning indicators
    if _count_indicators(text) < PREAMBLE_INDICATOR_THRESHOLD:
        return "", text

    # Split into sentences using punctuation boundaries
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())

    if len(sentences) <= 1:
        return "", text

    # Scan from the end to find where clean answer starts.
    # The last sentence with a reasoning indicator marks the boundary.
    answer_start_idx = len(sentences)

    for i in range(len(sentences) - 1, -1, -1):
        has_indicator = any(
            re.search(p, sentences[i]) for p in PREAMBLE_INDICATORS
        )
        if has_indicator:
            answer_start_idx = i + 1
            break

    # Safety: if boundary is at the very start or very end, skip
    if answer_start_idx >= len(sentences) or answer_start_idx == 0:
        return "", text

    reasoning_text = " ".join(sentences[:answer_start_idx]).strip()
    answer_text = " ".join(sentences[answer_start_idx:]).strip()

    # Don't return empty answer
    if not answer_text:
        return "", text

    return reasoning_text, answer_text


def _extract_reasoning_lines(text: str) -> tuple[list[str], str]:
    """Extract unstructured reasoning lines from text.

    These are plain-English reasoning lines that reasoning models
    sometimes produce without using explicit <think> tags.

    Args:
        text: Text after preamble and inline reasoning extraction.

    Returns:
        Tuple of (list of extracted reasoning lines, remaining text).
    """
    extracted: list[str] = []
    remaining = text

    for pattern in REASONING_LEAK_PATTERNS:
        matches = re.findall(pattern, remaining)
        for match in matches:
            stripped = match.strip()
            if stripped:
                extracted.append(stripped)
        remaining = re.sub(pattern, "", remaining).strip()

    return extracted, remaining


def _normalize_blank_lines(text: str) -> str:
    """Collapse repeated blank lines while preserving readable markdown.

    Args:
        text: Text that may have extra blank lines after cleanup.

    Returns:
        Text with at most one consecutive blank line.
    """
    lines = [line.rstrip() for line in text.splitlines()]
    cleaned_lines: list[str] = []
    previous_blank = False

    for line in lines:
        is_blank = not line.strip()
        if is_blank and previous_blank:
            continue
        cleaned_lines.append(line)
        previous_blank = is_blank

    return "\n".join(cleaned_lines).strip()


def _standardize_short_responses(text: str) -> str:
    """Normalize short clarification and limitation responses into
    consistent markdown headings.

    If the agent asks for clarification or states a tool limitation
    but does not use the standard heading format, this function wraps
    it in the correct heading.

    Args:
        text: Cleaned answer text.

    Returns:
        Text with standardized headings if applicable.
    """
    lower_text = text.lower()

    # Check for clarification patterns
    clarification_triggers = ["please provide", "please specify"]
    if any(trigger in lower_text for trigger in clarification_triggers):
        if not text.startswith("##"):
            return format_clarification(text)

    # Check for tool limitation patterns
    limitation_triggers = ["i don't have the required tools"]
    if any(trigger in lower_text for trigger in limitation_triggers):
        if not text.startswith("##"):
            return format_tool_limitation(text)

    return text


def separate_thinking_from_answer(raw_text: str) -> SeparatedResponse:
    """Extract reasoning/thinking text from raw LLM output and return
    a clean answer separately.

    This is the core function that solves the reasoning-leakage problem.
    It uses a 4-step extraction pipeline:

    1. Explicit <think>...</think> blocks (structured reasoning)
    2. Preamble detection (block of reasoning before newline)
    3. Inline reasoning extraction (sentence-level, no newline at all)
    4. Individual reasoning line patterns (known leak phrases)

    Steps 2 and 3 together handle three formats:
        - Reasoning separated by blank line (\\n\\n)
        - Reasoning separated by single newline (\\n)
        - Reasoning mixed with answer on one line (no newline)

    Args:
        raw_text: Raw LLM output that may contain reasoning.

    Returns:
        SeparatedResponse with thinking and answer separated.
    """
    if not raw_text:
        return SeparatedResponse(thinking="", answer="")

    thinking_parts: list[str] = []

    # Step 1: Extract explicit <think>...</think> blocks
    think_blocks, remaining = _extract_think_blocks(raw_text)
    thinking_parts.extend(think_blocks)

    # Step 2: Extract reasoning preamble (before newline)
    # Handles both \n\n (blank line) and \n (single newline)
    preamble, remaining = _extract_preamble(remaining)
    if preamble:
        thinking_parts.append(preamble)

    # Step 3: Extract inline reasoning (no newline at all)
    # Only runs if preamble detection did not extract anything.
    # This catches cases where reasoning and answer are in one
    # continuous paragraph with no newline separation.
    if not preamble:
        inline_reasoning, remaining = _extract_inline_reasoning(remaining)
        if inline_reasoning:
            thinking_parts.append(inline_reasoning)

    # Step 4: Extract individual unstructured reasoning lines
    # This catches any remaining known leak patterns
    reasoning_lines, remaining = _extract_reasoning_lines(remaining)
    thinking_parts.extend(reasoning_lines)

    # Step 5: Normalize the clean answer
    clean_answer = _normalize_blank_lines(remaining)

    # Step 6: Build thinking trace
    thinking_trace = "\n".join(thinking_parts).strip()

    return SeparatedResponse(
        thinking=thinking_trace,
        answer=clean_answer,
    )


def apply_output_guardrails(raw_text: str) -> SeparatedResponse:
    """Full output guardrail pipeline.

    This is the main output guardrail entry point. It runs after the
    ADK agent pipeline produces a raw response and before the response
    is sent to the frontend.

    Steps:
        1. Separate thinking from answer
        2. Redact PII in both thinking and answer
        3. Standardize short responses (clarification / limitation)
        4. Ensure safe fallback if answer is empty

    Args:
        raw_text: Raw LLM output from the ADK agent pipeline.

    Returns:
        SeparatedResponse with clean answer and preserved thinking.
    """
    if not raw_text:
        return SeparatedResponse(
            thinking="",
            answer=format_tool_limitation("No response was generated."),
        )

    # Step 1: Separate thinking from answer
    separated = separate_thinking_from_answer(raw_text)

    # Step 2: Redact PII in the answer
    answer = redact_sensitive_text(separated.answer)

    # Step 3: Standardize short responses
    answer = _standardize_short_responses(answer)

    # Step 4: Safe fallback
    if not answer.strip():
        answer = format_tool_limitation("No safe response was generated.")

    # Step 5: Redact PII in thinking trace too (defense in depth)
    thinking = redact_sensitive_text(separated.thinking)

    return SeparatedResponse(
        thinking=thinking,
        answer=answer,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Error guardrails
# ─────────────────────────────────────────────────────────────────────────────

def map_exception_to_user_message(exc: Exception) -> str:
    """Convert backend exceptions into short, user-facing safe responses.

    This avoids exposing stack traces, internal module paths, or raw
    exception text to the frontend. Instead, the user sees a short,
    actionable message.

    Args:
        exc: The caught exception from the agent pipeline.

    Returns:
        A short, safe, user-facing message string.
    """
    message = str(exc).strip().lower()

    if "confirm=true is required" in message:
        return format_clarification(
            "Please confirm whether I should proceed with the action."
        )

    if "customer_id is mandatory" in message:
        return format_clarification(
            "Please provide the customer ID in the format `CUST-###`."
        )

    if "not found" in message and "tool" in message:
        return format_tool_limitation()

    if "apiconnectionerror" in message or "connect" in message:
        return format_tool_limitation(
            "The AI model is currently unreachable. "
            "Please check if Ollama is running and try again."
        )

    return format_tool_limitation(
        "I couldn't complete that request due to a backend issue. "
        "Please try again or rephrase your question."
    )