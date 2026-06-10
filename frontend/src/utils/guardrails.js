/**
 * Frontend Guardrails — Input validation, rate limiting, XSS prevention.
 *
 * These guardrails run BEFORE any API call is made.
 * They complement the backend validators in app/utils/validators.py.
 *
 * Guardrails implemented:
 *   1. Input length validation (1-2000 chars, matches backend Pydantic schema)
 *   2. Empty/whitespace-only rejection
 *   3. Rate limiting (prevent rapid-fire submissions)
 *   4. HTML/script injection detection
 *   5. Max messages per session limit
 */

import { GUARDRAIL_LIMITS } from "./constants";

let lastSubmitTime = 0;

/**
 * Validates user input before sending to the API.
 * Returns { valid: boolean, error: string | null }
 */
export function validateQuery(query) {
  // 1. Empty or whitespace-only
  if (!query || !query.trim()) {
    return { valid: false, error: "Please enter a question." };
  }

  const trimmed = query.trim();

  // 2. Too short
  if (trimmed.length < GUARDRAIL_LIMITS.MIN_QUERY_LENGTH) {
    return { valid: false, error: "Query is too short." };
  }

  // 3. Too long (matches backend: max_length=2000 in ChatQueryRequest)
  if (trimmed.length > GUARDRAIL_LIMITS.MAX_QUERY_LENGTH) {
    return {
      valid: false,
      error: `Query is too long (${trimmed.length}/${GUARDRAIL_LIMITS.MAX_QUERY_LENGTH} characters).`,
    };
  }

  // 4. HTML/Script injection detection
  const dangerousPatterns = [
    /<script[\s>]/i,
    /<iframe[\s>]/i,
    /javascript:/i,
    /on\w+\s*=/i,
    /<img[^>]+onerror/i,
  ];
  for (const pattern of dangerousPatterns) {
    if (pattern.test(trimmed)) {
      return { valid: false, error: "Query contains invalid characters." };
    }
  }

  return { valid: true, error: null };
}

/**
 * Rate limiter — prevents rapid-fire API calls.
 * Returns { allowed: boolean, waitMs: number }
 */
export function checkRateLimit() {
  const now = Date.now();
  const elapsed = now - lastSubmitTime;

  if (elapsed < GUARDRAIL_LIMITS.RATE_LIMIT_MS) {
    const waitMs = GUARDRAIL_LIMITS.RATE_LIMIT_MS - elapsed;
    return { allowed: false, waitMs };
  }

  lastSubmitTime = now;
  return { allowed: true, waitMs: 0 };
}

/**
 * Checks if the session has exceeded the max message limit.
 */
export function checkMessageLimit(messageCount) {
  if (messageCount >= GUARDRAIL_LIMITS.MAX_MESSAGES_PER_SESSION) {
    return {
      allowed: false,
      error: `Session limit reached (${GUARDRAIL_LIMITS.MAX_MESSAGES_PER_SESSION} messages). Please refresh to start a new session.`,
    };
  }
  return { allowed: true, error: null };
}

/**
 * Sanitizes query text before display (defense-in-depth).
 * React already escapes JSX, but this adds an extra layer.
 */
export function sanitizeForDisplay(text) {
  if (!text) return "";
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}