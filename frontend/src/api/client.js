/**
 * TrafficTwin AI — API Client
 * Connects to the local FastAPI backend (http://127.0.0.1:8000)
 * with graceful fallback to authentic recorded simulation data.
 */

const API_BASE_URL = 'http://127.0.0.1:8000/api';

export async function apiRequest(endpoint, fallbackData = null) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      signal: controller.signal,
      headers: {
        'Accept': 'application/json',
      },
    });
    clearTimeout(timeoutId);

    if (!res.ok) {
      throw new Error(`API HTTP Error: ${res.status}`);
    }

    return await res.json();
  } catch (err) {
    // If backend is unreachable or timed out, gracefully return fallback data
    return fallbackData;
  }
}
