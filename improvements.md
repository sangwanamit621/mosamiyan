## Minor Observations & Recommendations for Phase 2

  1. HTTP Client Connection Reuse:
      • Current: httpx.AsyncClient is initialized with context managers inside provider request methods.
      • Recommendation for Phase 2: Introduce a shared singleton httpx.AsyncClient across the app lifespan for HTTP/2 connection pooling.
  2. Dynamic Timezone Labeling in Scrubber:
      • Current: Scrubber converts ISO timestamp strings using browser local formatting.
      • Recommendation for Phase 2: Use the API response timezone field with Intl.DateTimeFormat for exact searched location local time presentation.