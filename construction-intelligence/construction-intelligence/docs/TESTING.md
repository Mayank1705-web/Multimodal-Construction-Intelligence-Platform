# Testing

## Run

```bash
cd backend && python -m pytest -q       # backend tests
cd frontend && npm test                  # UI stability tests
```

Backend tests run offline with the mock provider, a temporary database and a patched weather call.

## Coverage by test type

| Type | What is verified |
|---|---|
| Functional | Each module returns a schema-valid result: safety, cracks, valuation, planning, assistant, weather, knowledge |
| End to end | The backend serves the built frontend; health, planning and error responses checked over HTTP |
| Contract | Success and error envelopes; cost parts add up to the total; every task starts after its dependencies; rooms stay inside the plot |
| AI output handling | Fenced or chatty JSON is extracted; one repair retry succeeds; two failures return invalid_ai_response; bad AI plans (absurd costs, cyclic tasks, overlapping rooms) are replaced and flagged |
| UI stability | Charts render with null, junk and valid data; the API client maps network failure, non-JSON and server errors to readable messages; each page sits inside an error boundary |
| Edge cases | Corrupt image, truncated PNG, empty file, unsupported type, six images, 60x60 image (warning), no input, negative area, unknown property type, empty city, unknown currency, zero plot width, 500 floors, unknown route |

## Manual checklist before a demo

1. Start with LLM_PROVIDER=mock and click through every module.
2. Switch to a real provider, upload a real site photo, and confirm the report matches what is visible.
3. Upload a half-downloaded image and confirm the error message appears and the form stays usable.
4. Stop the backend and confirm the UI shows the "Server not reachable" message.
5. Resize to a phone width and confirm the page does not scroll sideways.
6. Take a screenshot of each module for the submission.
