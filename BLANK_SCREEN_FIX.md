
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║                    🔴 BLANK SCREEN FIX GUIDE                              ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

## 🎯 ROOT CAUSE

The app.py blank screen is caused by one of these issues (in order of likelihood):

┌─────────────────────────────────────────────────────────────────────────┐
│ 1. ❌ Missing Streamlit Secrets (90% of cases)                           │
│    • App tries to connect to Databricks on line 179-195                 │
│    • Without secrets, it throws error and calls st.stop()               │
│    • Result: Blank screen (error might not display)                     │
│                                                                          │
│ 2. ❌ SQL Warehouse Not Running (5% of cases)                            │
│    • Connection times out                                                │
│    • App shows error and stops                                          │
│                                                                          │
│ 3. ❌ Missing Dependencies (3% of cases)                                 │
│    • databricks-sql-connector not installed                             │
│    • Import fails early                                                  │
│                                                                          │
│ 4. ❌ Empty FAQ Table (2% of cases)                                      │
│    • graphrag_common_qas has 0 rows                                      │
│    • Quick Start section empty (but page still renders)                 │
└─────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════

## 🔧 SOLUTION 1: Configure Secrets (Local Testing)

If you're testing LOCALLY with `streamlit run app.py`:

Step 1: Create secrets file
```bash
cd /Repos/muralimenon444@gmail.com/healthcare-policy-assistant/inference_interface
mkdir -p .streamlit
```

Step 2: Create .streamlit/secrets.toml
```toml
DATABRICKS_HOST = "dbc-XXXXXXXX-XXXX.cloud.databricks.com"
DATABRICKS_TOKEN = "dapiXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
DATABRICKS_WAREHOUSE_ID = "XXXXXXXXXXXXXXXX"
```

Step 3: Get your values from Databricks
• DATABRICKS_HOST: 
  → Go to Databricks workspace
  → Copy URL (e.g., dbc-a1b2c3-d4e5.cloud.databricks.com)
  → Remove https:// and any paths

• DATABRICKS_TOKEN:
  → Databricks → Settings → Developer → Access Tokens
  → "Generate New Token"
  → Copy token (starts with "dapi...")

• DATABRICKS_WAREHOUSE_ID:
  → Databricks → SQL Warehouses
  → Click your warehouse
  → Copy Warehouse ID from URL or settings

Step 4: Test connection
```bash
cd inference_interface
python diagnose_blank_screen.py
```

Step 5: Run app
```bash
streamlit run app.py
```

═══════════════════════════════════════════════════════════════════════════

## 🔧 SOLUTION 2: Configure Secrets (Streamlit Cloud)

If deploying to STREAMLIT CLOUD:

Step 1: Go to Streamlit Cloud dashboard
→ https://share.streamlit.io/

Step 2: Find your app
→ Click on "Healthcare Policy Assistant"

Step 3: Open Settings
→ Click "⋮" menu → "Settings"

Step 4: Add Secrets
→ Click "Secrets" tab
→ Paste this (with your actual values):

```toml
DATABRICKS_HOST = "dbc-XXXXXXXX-XXXX.cloud.databricks.com"
DATABRICKS_TOKEN = "dapiXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
DATABRICKS_WAREHOUSE_ID = "XXXXXXXXXXXXXXXX"
```

Step 5: Save and Reboot
→ Click "Save"
→ App will automatically restart
→ Wait 30-60 seconds

Step 6: Verify
→ Visit app URL
→ Should see landing page with Quick Start cards
→ If still blank, check logs (Settings → Logs)

═══════════════════════════════════════════════════════════════════════════

## 🔧 SOLUTION 3: Check SQL Warehouse

If secrets are configured but still blank:

Step 1: Verify SQL Warehouse is RUNNING
→ Databricks → SQL Warehouses
→ Your warehouse should show "Running" (green)
→ If "Stopped", click "Start"

Step 2: Test connection manually
```python
from databricks import sql

connection = sql.connect(
    server_hostname="dbc-XXXXXXXX-XXXX.cloud.databricks.com",
    http_path="/sql/1.0/warehouses/XXXXXXXXXXXXXXXX",
    access_token="dapiXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
)

cursor = connection.cursor()
cursor.execute("SELECT COUNT(*) FROM research_catalog.healthcare.graphrag_common_qas")
result = cursor.fetchone()
print(f"FAQ count: {result[0]}")
cursor.close()
```

═══════════════════════════════════════════════════════════════════════════

## 🔧 SOLUTION 4: Check Dependencies

Ensure all packages installed:

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install streamlit>=1.28.0
pip install databricks-sql-connector>=3.0.0
pip install pandas
pip install openai
pip install networkx
pip install matplotlib
```

═══════════════════════════════════════════════════════════════════════════

## 🔧 SOLUTION 5: Seed FAQ Table (if empty)

If graphrag_common_qas table is empty:

```sql
-- Run in Databricks SQL Editor
INSERT INTO research_catalog.healthcare.graphrag_common_qas 
(id, question, answer, entities, last_updated, source)
VALUES
  (uuid(), 'what is medicare part a', 'Medicare Part A covers hospital insurance...', '["Medicare Part A"]', current_timestamp(), 'manual_seed'),
  (uuid(), 'what is medicare part b', 'Medicare Part B covers medical insurance...', '["Medicare Part B"]', current_timestamp(), 'manual_seed'),
  (uuid(), 'what is medicare part d', 'Medicare Part D covers prescription drugs...', '["Medicare Part D"]', current_timestamp(), 'manual_seed'),
  (uuid(), 'what is medicare advantage', 'Medicare Advantage (Part C) is an alternative...', '["Medicare Advantage"]', current_timestamp(), 'manual_seed');
```

═══════════════════════════════════════════════════════════════════════════

## ✅ VERIFICATION CHECKLIST

After applying fixes, verify:

Landing Page (should load in <1 second):
  □ Header: "🏥 Medicare Policy Assistant"
  □ Search bar visible
  □ Quick Start section with 4 cards
  □ Sidebar shows "Cached FAQs: XXX"

Click Quick Start Button:
  □ Instant answer appears (<100ms)
  □ Badge: "⚡ Instant Answer (from cache)"
  □ No spinner/loading

New Search:
  □ Enter question
  □ Shows "🔍 Analyzing your question..." spinner
  □ Answer appears with tabs
  □ Shows "✅ Answer cached for future queries"

Logs (if still failing):
  □ Check Streamlit logs for exact error
  □ Look for "Missing secret: ..." or "Connection failed: ..."

═══════════════════════════════════════════════════════════════════════════

## 🐛 STILL BLANK? Debug Steps

1. Run diagnostic script:
   ```bash
   cd inference_interface
   python diagnose_blank_screen.py
   ```

2. Check Streamlit logs:
   • Local: Terminal output
   • Cloud: Settings → Logs

3. Test minimal version:
   ```python
   import streamlit as st
   st.write("Hello World")
   ```
   
   If this works, problem is in app.py logic
   If this fails, problem is environment/secrets

4. Check error location:
   • Line 27: Missing databricks-sql-connector
   • Line 191-195: Missing/invalid secrets
   • Line 270-272: Empty Delta tables
   
═══════════════════════════════════════════════════════════════════════════

## 📞 SUPPORT

If still stuck:
  1. Check error in logs (Settings → Logs in Streamlit Cloud)
  2. Run: python diagnose_blank_screen.py
  3. Share exact error message
  4. Verify secrets format (no quotes, correct values)

Common mistakes:
  ❌ DATABRICKS_HOST includes https:// (remove it)
  ❌ Token has spaces or newlines (copy carefully)
  ❌ Warehouse ID is name instead of ID (use ID)
  ❌ Secrets not saved (click Save button)

═══════════════════════════════════════════════════════════════════════════

💡 TIP: The most common fix is configuring secrets. 90% of blank screens
        are caused by missing DATABRICKS_HOST, TOKEN, or WAREHOUSE_ID.

═══════════════════════════════════════════════════════════════════════════
