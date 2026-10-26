import { useCallback, useRef, useState } from "react";
import { ApiError } from "./api.js";

const TITLES = {
  network: "Server not reachable",
  corrupt_image: "Image could not be read",
  unsupported_image: "Unsupported image type",
  no_input: "More input needed",
  invalid_ai_response: "AI response rejected",
  llm_unavailable: "AI service unavailable",
  llm_not_configured: "AI service not configured",
  weather_unavailable: "Weather unavailable",
  location_not_found: "Location not found",
};

// Runs an API call and tracks loading, result and error. Ignores results from superseded calls.
export function useAnalysis() {
  const [state, setState] = useState({ loading: false, result: null, error: null });
  const ticket = useRef(0);

  const run = useCallback(async (fn) => {
    const mine = ++ticket.current;
    setState({ loading: true, result: null, error: null });
    try {
      const body = await fn();
      if (mine === ticket.current) setState({ loading: false, result: body, error: null });
    } catch (e) {
      if (mine !== ticket.current) return;
      const err = e instanceof ApiError ? e : new ApiError("unknown", "An unexpected error occurred.", 0);
      setState({ loading: false, result: null, error: { title: TITLES[err.code] || "Request failed", message: err.message } });
    }
  }, []);

  const reset = useCallback(() => {
    ticket.current++;
    setState({ loading: false, result: null, error: null });
  }, []);

  return { ...state, run, reset };
}
