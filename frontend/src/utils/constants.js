/**
 * Application constants — FAQ data, config, and guardrail limits.
 *
 * Architecture Mapping:
 *   FAQSection.jsx reads FAQ_QUESTIONS from here.
 *   guardrails.js reads limits from here.
 *   chatApi.js reads API_BASE_URL from env.
 */

export const FAQ_QUESTIONS = [
  // ── 🔵 Observability Queries ────────────────────────────────
  {
    category: "Observability",
    icon: "📊",
    questions: [
      "What is the error rate for payment-service in the last 24 hours?",
      "Show me alerts for payment-service",
      "What is the p95 latency for payment-service?",
      "Show me logs for checkout-service",
      "What is the throughput for payment-service?",
    ],
  },
  // ── 🟢 Business Queries ─────────────────────────────────────
  {
    category: "Business",
    icon: "💼",
    questions: [
      "Show me orders for customer CUST-001",
      "Get the profile of customer CUST-002",
      "Show me declined transactions for yesterday",
      "Show me approved transactions for today",
    ],
  },
  // ── 🔴 Action Queries ───────────────────────────────────────
  {
    category: "Actions",
    icon: "⚙️",
    questions: [
      "Restart payment-service",
      "Scale checkout-service to 3 replicas",
      "Create a ticket for payment gateway failures with high priority",
    ],
  },
  // ── 🔀 Cross-Domain Queries ─────────────────────────────────
  {
    category: "Cross-Domain",
    icon: "🔀",
    questions: [
      "Why did revenue drop yesterday?",
      "What is the business impact of payment-service errors?",
      "Compare system errors with declined transactions",
    ],
  },
];

export const GUARDRAIL_LIMITS = {
  MAX_QUERY_LENGTH: 2000,
  MIN_QUERY_LENGTH: 1,
  RATE_LIMIT_MS: 2000,
  MAX_MESSAGES_PER_SESSION: 100,
};

export const APP_CONFIG = {
  APP_NAME: "Multi-System Data Assistant",
  APP_SUBTITLE: "Google ADK + MCP",
  PLACEHOLDER: "Ask about revenue, customer impact, logs, metrics, alerts, or safe actions.",
};