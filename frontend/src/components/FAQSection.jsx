/**
 * FAQSection — Displays categorized frequently asked questions.
 *
 * Clicking a question auto-fills and submits it to the chat.
 * Categories match the 3 MCP servers + cross-domain queries.
 *
 * Architecture Mapping:
 *   FAQSection → onSelectQuestion(query) → useChat.submitQuery() → Backend
 */

import { FAQ_QUESTIONS } from "../utils/constants";

export default function FAQSection({ onSelectQuestion, disabled }) {
  return (
    <div className="faq-section">
      <h3 className="faq-title">💡 Try asking...</h3>
      <div className="faq-grid">
        {FAQ_QUESTIONS.map((category) => (
          <div key={category.category} className="faq-category">
            <h4 className="faq-category-title">
              {category.icon} {category.category}
            </h4>
            <div className="faq-questions">
              {category.questions.map((question) => (
                <button
                  key={question}
                  className="faq-chip"
                  onClick={() => onSelectQuestion(question)}
                  disabled={disabled}
                  title={question}
                >
                  {question.length > 55 ? question.slice(0, 55) + "…" : question}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}