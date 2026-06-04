const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function sendChatQuery(query, confirmAction = false) {
  const response = await fetch(`${API_BASE_URL}/chat/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, confirm_action: confirmAction }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown API error' }));
    throw new Error(error.detail || error.error || 'Chat request failed');
  }
  return response.json();
}
