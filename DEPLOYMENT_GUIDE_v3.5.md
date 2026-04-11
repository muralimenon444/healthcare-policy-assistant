# v3.5 Quick Deployment Guide

## 🚀 5-Minute Deployment

### Prerequisites
✅ Databricks SQL Warehouse running  
✅ Unity Catalog tables populated (`research_catalog.healthcare.graphrag_*`)  
✅ Streamlit Cloud account connected to GitHub  

---

## Step 1: Verify Delta Tables

```sql
-- Run in Databricks SQL Editor
USE CATALOG research_catalog;
USE SCHEMA healthcare;

-- Check tables exist
SHOW TABLES;

-- Verify data
SELECT COUNT(*) as entity_count FROM graphrag_entities;
SELECT COUNT(*) as relationship_count FROM graphrag_relationships;
SELECT COUNT(*) as text_unit_count FROM graphrag_text_units;
SELECT COUNT(*) as faq_count FROM graphrag_common_qas;
```

**Expected Output:**
- `graphrag_entities`: >1000 rows
- `graphrag_relationships`: >3000 rows
- `graphrag_text_units`: >500 rows
- `graphrag_common_qas`: >20 rows (minimum)

⚠️ **If `graphrag_common_qas` is empty:**
```sql
-- Quick seed with sample FAQs
INSERT INTO graphrag_common_qas VALUES
('uuid1', 'what is medicare part a', 'Medicare Part A covers hospital insurance...', '["Medicare Part A"]', current_timestamp(), 'manual_seed'),
('uuid2', 'what is medicare part b', 'Medicare Part B covers medical insurance...', '["Medicare Part B"]', current_timestamp(), 'manual_seed'),
('uuid3', 'what is medicare part d', 'Medicare Part D covers prescription drugs...', '["Medicare Part D"]', current_timestamp(), 'manual_seed');
```

---

## Step 2: Configure Secrets

### Local Testing (Optional)
```bash
cd inference_interface
mkdir -p .streamlit
cat > .streamlit/secrets.toml << EOF
DATABRICKS_HOST = "your-workspace.cloud.databricks.com"
DATABRICKS_TOKEN = "dapi1234567890..."
DATABRICKS_WAREHOUSE_ID = "abc123def456"
EOF
```

### Streamlit Cloud (Required)
1. Go to **Streamlit Cloud** → Your App → **Settings** → **Secrets**
2. Paste:
```toml
DATABRICKS_HOST = "your-workspace.cloud.databricks.com"
DATABRICKS_TOKEN = "dapi1234567890..."
DATABRICKS_WAREHOUSE_ID = "abc123def456"
```

**How to get values:**
- **DATABRICKS_HOST**: From URL (e.g., `dbc-a1b2c3d4-ef56.cloud.databricks.com`)
- **DATABRICKS_TOKEN**: Workspace → Settings → Developer → Access Tokens → Generate New Token
- **DATABRICKS_WAREHOUSE_ID**: SQL Warehouses → Your Warehouse → Connection Details → Server Hostname (extract ID)

---

## Step 3: Deploy App

### Option A: Local Test First (Recommended)
```bash
cd /Repos/muralimenon444@gmail.com/healthcare-policy-assistant/inference_interface

# Install dependencies
pip install -r requirements.txt

# Test connection
python test_connection.py  # (create this if needed)

# Run app
streamlit run app.py

# Open browser: http://localhost:8501
```

**Verify:**
- ✅ Page loads in <1 second
- ✅ Quick Start cards visible
- ✅ Click Quick Start → instant answer
- ✅ New search → "Analyzing..." spinner → answer

### Option B: Direct Deploy to Streamlit Cloud
```bash
cd healthcare-policy-assistant

# Commit v3.5
git add inference_interface/app.py
git add README_v3.5.md
git add CHANGELOG.md
git commit -m "v3.5: Lazy loading + pre-cache + write-back"

# Push
git push origin main
```

**Streamlit Cloud Auto-Deploys:**
1. Detects push to `main`
2. Pulls latest code
3. Installs `requirements.txt`
4. Restarts app
5. Live in ~2 minutes

---

## Step 4: Verify Production

### Checklist
Visit your Streamlit Cloud app URL and verify:

#### Landing Page (<1 second load)
- [ ] 🏥 Header displays: "Medicare Policy Assistant"
- [ ] 🔍 Search bar visible
- [ ] ⚡ Quick Start section with 4 cards
- [ ] 📊 Sidebar shows "Cached FAQs: X"

#### Quick Start (Instant)
- [ ] Click any Quick Start button
- [ ] Answer appears in <100ms
- [ ] Shows "⚡ **Instant Answer** (from cache)"
- [ ] No spinner/loading indicator

#### New Search (5-8 seconds)
- [ ] Enter new question
- [ ] Click Search button
- [ ] Shows "🔍 Analyzing your question..." spinner
- [ ] Answer displays with tabs: Analysis / Graph / Evidence
- [ ] Caption shows "✅ Answer cached for future queries"

#### Repeat Search (Instant)
- [ ] Go back to landing
- [ ] Search same question again
- [ ] Answer appears in <100ms (from cache)

#### Error Handling
- [ ] Invalid question → graceful error message
- [ ] No internet → connection error message
- [ ] Rate limit → "🚫 Rate limit exceeded" message

---

## Step 5: Monitor Performance

### Streamlit Logs
```bash
# Check app logs in Streamlit Cloud
# Look for:
✅ "PHASE 1: Instant UI" (should be <1s)
✅ "PHASE 2: On-demand search" (only when user searches)
✅ "Write-back successful" (after new searches)
```

### Databricks SQL Warehouse
1. Go to **SQL Warehouses** → Your Warehouse → **Query History**
2. Verify:
   - Initial load: Only 1 query (`SELECT * FROM graphrag_common_qas`)
   - After search: 4 queries (entities, relationships, text_units, common_qas)
   - Repeat search: 0 queries (from cache)

### Cache Performance
Add to sidebar in app.py (optional):
```python
# In sidebar
if 'query_count' not in st.session_state:
    st.session_state.query_count = 0

st.metric("Queries This Session", st.session_state.query_count)
st.metric("Cache Hit Rate", f"{cache_hit_rate:.1%}")
```

---

## Troubleshooting

### Issue: "No Quick Start questions available"
**Cause:** `graphrag_common_qas` table empty

**Fix:**
```sql
-- Run seed query from Step 1
INSERT INTO graphrag_common_qas VALUES (...);
```

### Issue: Page takes 5+ seconds to load
**Cause:** Full graph loading on startup (v3.4 behavior)

**Fix:**
1. Verify you deployed v3.5 app.py (check header comment)
2. Check for `load_common_qas_quick()` function
3. Ensure `load_full_graph()` only called on search

### Issue: "Failed to connect to Databricks"
**Cause:** Invalid secrets or SQL Warehouse stopped

**Fix:**
1. Verify secrets in Streamlit Cloud settings
2. Start SQL Warehouse in Databricks
3. Check token hasn't expired

### Issue: "Answer cached" message doesn't appear
**Cause:** Write-back failing silently

**Fix:**
1. Check SQL Warehouse permissions:
   ```sql
   GRANT INSERT ON TABLE research_catalog.healthcare.graphrag_common_qas 
   TO `your-service-principal`;
   ```
2. Verify SQL Warehouse running
3. Check app logs for error messages

### Issue: Repeat questions not instant
**Cause:** Cache not working

**Fix:**
1. Check `@st.cache_data(ttl=3600)` decorators present
2. Verify `load_common_qas_quick.clear()` called after write-back
3. Check Streamlit session state not resetting

---

## Rollback Plan

If v3.5 has issues:

```bash
# Restore v3.4
cd healthcare-policy-assistant
git revert HEAD
git push origin main

# Or restore from backup
cp inference_interface/app_v3.4_backup.py inference_interface/app.py
git add inference_interface/app.py
git commit -m "Rollback to v3.4"
git push origin main
```

**No data loss:** v3.5 is fully backward compatible

---

## Success Metrics

After 24 hours of production use:

| Metric | Target | How to Check |
|--------|--------|--------------|
| **Page Load Time** | <1 second | Streamlit logs |
| **Cache Hit Rate** | >60% | SQL query history |
| **Quick Start Response** | <100ms | User testing |
| **New FAQ Growth** | +10-20/day | `SELECT COUNT(*) FROM graphrag_common_qas WHERE source='on_demand_graphrag'` |
| **Error Rate** | <1% | Streamlit error logs |

---

## Next Steps

### Week 1: Monitor
- Check cache hit rate daily
- Review `common_qas` table growth
- Gather user feedback

### Week 2: Optimize
- Adjust fuzzy match threshold if needed
- Add popular questions to Quick Start
- Fine-tune cache TTL

### Week 3: Enhance
- Plan v3.6 features (user feedback, smart pre-fetch)
- Consider multi-tenancy if needed
- Implement analytics dashboard

---

## Support

**Deployment Issues:** muralimenon444@gmail.com  
**Databricks Support:** [Internal Slack Channel]  
**Streamlit Cloud Docs:** https://docs.streamlit.io/streamlit-community-cloud  

---

**Deployment Time:** ~5 minutes  
**Zero Downtime:** ✅  
**Rollback Available:** ✅  

**Last Updated:** 2026-04-11
