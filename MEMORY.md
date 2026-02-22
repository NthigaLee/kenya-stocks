# MEMORY.md - Long-Term Memory

_Last updated: 2026-02-22_

---

## Who I Am

- **Name:** MseeBot 🌍
- **Identity file:** `IDENTITY.md`
- **Soul:** Warm, direct, a bit playful. Technical when needed, relaxed most of the time. Kenyan-flavoured vibe.

---

## Who Lee Is

- **Name:** Lee (msee)
- **From:** Kenya, currently living in Bermuda
- **Timezone:** Bermuda (AST, UTC-4)
- **Vibe:** Relaxed, comfortable with Kenyan slang, prefers concise and friendly replies
- **Contact:** Telegram connected ✅

---

## Setup Status (as of 2026-02-22)

### ✅ Done
- OpenClaw installed and running on Windows (i7, 16GB RAM, 1TB storage)
- Telegram connected and working
- Brave Search API key configured ✅
- LM Studio installed with the following models loaded:
  - `meta-llama-3.1-8b-instruct` (primary local chat model)
  - `llama-3.2-1b-instruct`
  - `google/gemma-3-4b`
  - `text-embedding-nomic-embed-text-v1.5` (local embeddings backup)
- LM Studio server running on `http://localhost:1234`
- GPU Offload set to 0 (CPU only — no dedicated GPU on this machine)
- OpenClaw configured to use LM Studio as fallback LLM

### ⚠️ Pending / In Progress
- **LM Studio context window** — needs to be set to 16384+ for the 8B model (Lee was confirming)
- **OpenAI API credits** — quota exceeded, needs top-up for embedding-based memory search
  - Top-up page: https://platform.openai.com/settings/organization/billing
  - Once topped up, semantic memory search (memory_search tool) will work again
- **BOOTSTRAP.md** — still exists in workspace, should be deleted once setup is fully confirmed

---

## How to Continue After a Model Switch

If a new model is loaded or the session restarts fresh:

1. Read `SOUL.md` — personality and values
2. Read `USER.md` — who Lee is
3. Read `IDENTITY.md` — who I am
4. Read `MEMORY.md` (this file) — current state of work
5. Read today's daily note in `memory/YYYY-MM-DD.md`
6. Check `HEARTBEAT.md` for any active tasks

The workspace files are the source of truth. Any model can pick up from here.

---

## Key Config Details

| Setting | Value |
|---|---|
| LM Studio URL | http://localhost:1234/v1 |
| LM Studio model | meta-llama-3.1-8b-instruct |
| LM Studio API key | lm-studio (placeholder) |
| OS | Windows 10 (x64) |
| Shell | PowerShell (pwsh) |
| Node | v24.13.1 |

---

## Lessons Learned

- LM Studio on this machine needs **GPU Offload = 0** (no dedicated GPU)
- Context window must be set to **16384+** in LM Studio for OpenClaw compatibility
- OpenAI embeddings quota can run out — always good to have local embeddings (`nomic-embed-text`) as backup
- Web search needs Brave API key — free tier (2000 req/month) is enough for normal use

---

## Kenya Stocks Project (as of 2026-02-22)

### Key Files
- `kenya-stocks/FRONTEND.md` — UI anatomy reference (how to make changes on command)
- `kenya-stocks/COMPANY_NOTES.md` — Deep per-company financial reference (ABSA, StanChart, Safaricom)
- `kenya-stocks/backend/audit_company_pdfs.py` — PDF audit script
- `kenya-stocks/data/nse/financials.json` — Extracted financials (partially complete)
- `kenya-stocks/data/nse/financials.xlsx` — Same data in Excel

### Current Data Status
- **ABSA**: 9 PDFs, 9 JSON entries — Group + Company. Extraction partially broken (note numbers grabbed instead of values)
- **StanChart**: 8 PDFs, only 6 in JSON. Missing: FY2024 and H1 FY2025. Good data for FY2023 onwards
- **Safaricom**: 4 PDFs found by audit (2 more missed due to uppercase filename bug), only 3 in JSON. FY2024 data available. Reports in KES millions (not thousands)

### Known Extraction Bugs to Fix
1. Note reference numbers captured instead of actual values
2. Multi-column numbers concatenated (e.g. "568,015 490,128" → 568015490128)
3. PAT sign error (picks up equity movement, not P&L)
4. Safaricom UPPERCASE filenames missed by audit script

### Next Steps
- [ ] Send Lee screenshot of desired UI → implement changes
- [ ] Fix extraction bugs and re-run for all 3 companies
- [ ] Add FY2024/H1 FY2025 StanChart to JSON
- [ ] Add FY2023/FY2024 Safaricom to JSON

---

## Things To Do / Follow Up

- [ ] Top up OpenAI credits (https://platform.openai.com/settings/organization/billing)
- [ ] Confirm LM Studio context window is set to 16384+
- [ ] Delete `BOOTSTRAP.md` once setup is fully stable
- [ ] Configure OpenClaw to use `text-embedding-nomic-embed-text-v1.5` for local embeddings fallback
