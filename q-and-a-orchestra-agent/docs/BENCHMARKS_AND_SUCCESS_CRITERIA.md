# Industry Benchmarks & Success Criteria for Email Enrichment (2025)

## 1. Industry Standards (B2B Email Finding)
Based on 2025 benchmark reports from *Anymail Finder*, *Dropcontact*, and *PhantomBuster*, the following standards define "High Performance" in the email enrichment industry.

### 📊 Key Metrics

| Metric | Definition | Gold Standard (Top Tier) | Industry Average | Low Performance |
| :--- | :--- | :--- | :--- | :--- |
| **Match Rate** | % of input contacts where a valid email is found. | **70% - 80%** | **50% - 65%** | < 40% |
| **Accuracy** | % of found emails that do not hard bounce. | **> 95%** | **85% - 90%** | < 75% |
| **Speed (Live)** | Time to enrich one contact using live web/waterfall. | **3 - 5 seconds** | **10 - 20 seconds** | > 30 seconds |
| **Speed (DB)** | Time to enrich one contact using cached/database. | **< 0.5 seconds** | **~1 second** | N/A |

*   **Context for RECA**: Our system is a **Hybrid (Database + Live Scraping)**.
    *   *Database/Pattern* hits should be near instant.
    *   *Live Scraping* (Gemini/Web) will be slower but higher quality for hard targets.
    *   **Target Speed**: Average **< 10 seconds** per contact (blended).

### 🏆 Benchmark References
*   **Anymail Finder (2025)**: Achieved ~78% match rate on "Company Name + Person Name" inputs.
*   **Dropcontact**: Rated #1 for accuracy, utilizing a proprietary live enrichment engine (similar to our architectural goal).
*   **PhantomBuster**: ~3s per lead for waterfall enrichment.

---

## 2. RECA Success Criteria (Scale Test 1)

For our first "Large Batch" run (50 Agents), we will measure against these targets to determine pass/fail status.

### 🎯 Success Targets

| Metric | Target | Minimum Acceptable | Measurement Method |
| :--- | :--- | :--- | :--- |
| **Fill Rate** | **> 60%** | **40%** | `(Emails Found / Total Processed)` |
| **Throughput** | **< 8s / agent** | **< 15s / agent** | `Total Duration / Total Processed` |
| **Error Rate** | **< 5%** | **< 10%** | `(Exceptions / Total Processed)` |
| **Cost Efficiency** | **< $0.01 / agent** | **< $0.03 / agent** | `Total LLM Cost / Total Processed` |

### 🔍 Qualitative Checks
1.  **Brokerage Match**: Did the extracted email domain match the brokerage (or valid personal provider like gmail/yahoo if common)?
2.  **Pattern Usage**: Did the system learn new patterns from the batch?
3.  **Rate Limiting**: Did we hit any `429 Too Many Requests` errors from Google/Gemini?

---

## 3. Test Procedure
1.  **Input**: Random sample of 50 "Licensed" agents with "Brokerage" data from `all_agents.json`.
2.  **Execution**: Run `test_scale_batch.py`.
3.  **Analysis**:
    *   Compare `Fill Rate` vs Industry (Aiming for that 60-70% range).
    *   Check `logs` for Rate Limit warnings.
    *   Calculate `Cost per Success`.

*This document serves as the "Measurable Scale of Comparison" for the upcoming test run.*
