/**
 * ActionConfirmation — Info banner for action-type queries.
 *
 * NOTE: Confirmation is now handled at the AGENT CONVERSATION level.
 * The Action Agent asks "Shall I proceed?" and the user replies "Yes".
 * This component simply shows an informational notice.
 *
 * Architecture Mapping:
 *   Action Agent instruction → asks user for confirmation in chat →
 *   user replies "Yes" → agent calls tool with confirm=True
 */

export default function ActionConfirmation({ visible }) {
  if (!visible) return null;

  return (
    <div className="confirmation">
      <p>
        ⚠️ <strong>Action queries</strong> (restart, scale, create ticket) require
        confirmation. The agent will ask you to confirm before executing any action.
        Simply reply <strong>"Yes"</strong> or <strong>"Confirm"</strong> in the chat.
      </p>
    </div>
  );
}