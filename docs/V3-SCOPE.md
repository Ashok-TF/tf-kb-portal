# V3 Scope — Enterprise KB Platform

Post-v2 roadmap with suggested owners and estimates.

| ID | Task | Owner | Est. Hours | Dependencies |
|----|------|-------|------------|--------------|
| V3.1 | Full sources + artifact registry (URL assets, versioning) | Backend lead | 80–100 | v2 complete |
| V3.2 | Vision-LLM for diagrams/UML/flowcharts | Backend + ML | 100–120 | V3.1, OpenAI vision budget |
| V3.3 | Knowledge graph (entities + relationships in Postgres/Neo4j) | Backend lead | 120–160 | V3.2 enrichment quality |
| V3.4 | Graph / wiki / context search strategies | Backend lead | 80–100 | V3.3 |
| V3.5 | Advanced multi-KB parallel fusion + re-rank | Backend lead | 60–80 | V3.4 (v1 has basic agent) |
| V3.6 | Analytics dashboards + Confluence/GitHub connectors | Full stack | 100–140 | v2 governance, Entra ID |

**Total rough estimate:** 540–700 hours (~4–5 months with 2 FTE)

**Go/no-go:** Start V3 only after v2 demo metrics (search quality, adoption, connector demand).
