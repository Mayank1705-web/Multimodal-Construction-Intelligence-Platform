# API reference

Base URL: `http://localhost:8000`. Interactive documentation is served at `/docs` (Swagger UI).

## Response contract

Every endpoint returns one of two shapes.

Success:

```json
{
  "status": "success",
  "data": { },
  "meta": { "request_id": "a1b2c3d4e5f6", "provider": "anthropic", "latency_ms": 2310, "record_id": 12, "warnings": [] }
}
```

Error (the HTTP status matches the failure):

```json
{ "status": "error", "error": { "code": "corrupt_image", "message": "site.png is corrupt or incomplete and could not be read. Re-export or re-upload the image." } }
```

`data` is validated against the Pydantic models in `backend/app/schemas.py` before it is returned.

## Endpoints

| Method | Path | Input | Purpose |
|---|---|---|---|
| GET | /api/health | none | Provider and demo-mode status |
| POST | /api/safety/analyze | multipart: `description`, `site_type`, `images[]` (max 4) | Hazards, PPE, corrective actions |
| POST | /api/cracks/analyze | multipart: `description`, `element_type`, `age_months`, `images[]` | Crack type, severity, causes, actions |
| POST | /api/valuation/estimate | JSON `ValuationRequest` | Value range and factors |
| POST | /api/planning/generate | JSON `PlanRequest` | Layout, materials, cost, schedule |
| POST | /api/assistant/daily | JSON `AssistantRequest` | Checklist and warnings |
| POST | /api/weather/advisory | JSON `WeatherRequest` | Live forecast and activity advice |
| POST | /api/knowledge/ask | JSON `KnowledgeRequest` | Technical answer and standards to check |
| GET | /api/history?kind=&limit= | query | Saved analyses |
| GET | /api/history/{id} | path | One saved analysis with request and result |
| DELETE | /api/history/{id} | path | Delete a record |

## Error codes

| Code | HTTP | Meaning |
|---|---|---|
| no_input | 422 | No image and fewer than 10 characters of text |
| invalid_request | 422 | A field failed validation (the message names the field) |
| corrupt_image | 422 | Image is truncated, damaged or not an image |
| empty_image | 422 | Zero-byte file |
| unsupported_image | 415 | Not JPEG, PNG or WebP |
| image_too_large | 413 | Larger than MAX_IMAGE_MB |
| too_many_images | 422 | More than MAX_IMAGES_PER_REQUEST |
| unsupported_currency | 422 | Currency not in INR, USD, EUR, GBP, AED |
| location_not_found | 404 | Weather geocoding returned nothing |
| weather_unavailable | 502 | Open-Meteo unreachable or returned unexpected data |
| llm_not_configured | 503 | Missing API key or model id |
| llm_unavailable | 502 | Provider call failed (network, auth, rate limit) |
| invalid_ai_response | 502 | Model output failed schema validation twice |
| not_found | 404 | Unknown history record |
| internal_error | 500 | Unexpected server fault |

## Safeguards applied after the model replies (planning)

The platform does not trust model arithmetic or geometry.

- Material totals, the cost breakdown and cost per sq ft are recomputed from quantities and unit costs.
- If the model's material cost is outside 0.5x to 2x of the platform baseline, the baseline is used and a warning is returned.
- Task start and end days are recomputed from dependencies. Cycles or unknown dependencies trigger a standard schedule and a warning.
- Rooms must fit inside the plot and must not overlap. Otherwise a standard layout is used and a warning is returned.
