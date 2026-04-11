
"""
Diagnostic Script for Healthcare Policy Assistant v3.5
Run this BEFORE running app.py to identify issues
"""

import sys

print("="*80)
print("🔍 HEALTHCARE POLICY ASSISTANT v3.5 - DIAGNOSTICS")
print("="*80)

# Check 1: Streamlit installed
print("\n1. Checking Streamlit...")
try:
    import streamlit as st
    print(f"   ✅ Streamlit installed: v{st.__version__}")
except ImportError:
    print("   ❌ Streamlit NOT installed")
    print("      Run: pip install streamlit")
    sys.exit(1)

# Check 2: Databricks SQL connector
print("\n2. Checking Databricks SQL connector...")
try:
    from databricks import sql
    print("   ✅ databricks-sql-connector installed")
except ImportError:
    print("   ❌ databricks-sql-connector NOT installed")
    print("      Run: pip install databricks-sql-connector>=3.0.0")
    sys.exit(1)

# Check 3: Other dependencies
print("\n3. Checking other dependencies...")
required = {
    'pandas': 'pandas',
    'networkx': 'networkx',
    'matplotlib': 'matplotlib',
    'openai': 'openai'
}

for name, package in required.items():
    try:
        __import__(package)
        print(f"   ✅ {name} installed")
    except ImportError:
        print(f"   ⚠️  {name} NOT installed (optional)")

# Check 4: Streamlit secrets
print("\n4. Checking Streamlit secrets...")
print("   ⚠️  Cannot check secrets from here")
print("   ℹ️  If running locally: create .streamlit/secrets.toml")
print("   ℹ️  If on Streamlit Cloud: configure in Settings → Secrets")
print("")
print("   Required secrets:")
print("   - DATABRICKS_HOST")
print("   - DATABRICKS_TOKEN")
print("   - DATABRICKS_WAREHOUSE_ID")

# Check 5: Delta tables
print("\n5. Checking Delta tables...")
try:
    # This will only work in Databricks environment
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()
    
    tables = [
        "research_catalog.healthcare.graphrag_entities",
        "research_catalog.healthcare.graphrag_relationships",
        "research_catalog.healthcare.graphrag_text_units",
        "research_catalog.healthcare.graphrag_common_qas"
    ]
    
    for table in tables:
        try:
            count = spark.sql(f"SELECT COUNT(*) as c FROM {table}").collect()[0]['c']
            if count > 0:
                print(f"   ✅ {table}: {count:,} rows")
            else:
                print(f"   ⚠️  {table}: EMPTY")
        except Exception as e:
            print(f"   ❌ {table}: ERROR - {str(e)[:50]}")
except:
    print("   ⚠️  Cannot check (not in Databricks environment)")
    print("   ℹ️  Tables will be checked via SQL Warehouse connection")

print("\n" + "="*80)
print("📊 DIAGNOSTIC SUMMARY")
print("="*80)

print("""
If you're seeing a BLANK SCREEN, the most likely causes are:

1. 🔴 MISSING SECRETS (Most Common)
   → Configure Databricks credentials in Streamlit secrets
   → Local: .streamlit/secrets.toml
   → Cloud: App Settings → Secrets

2. 🟡 SQL WAREHOUSE NOT RUNNING
   → Start your SQL Warehouse in Databricks
   → Check warehouse ID is correct

3. 🟡 EMPTY graphrag_common_qas TABLE
   → Run: SELECT * FROM research_catalog.healthcare.graphrag_common_qas;
   → Should have at least 10-20 FAQs for Quick Start

4. 🟡 NETWORK/FIREWALL ISSUES
   → Streamlit Cloud needs to reach Databricks
   → Check IP whitelist if using private endpoints

═══════════════════════════════════════════════════════════════════════════

🚀 NEXT STEPS:

If running LOCALLY:
  1. Create .streamlit/secrets.toml with Databricks credentials
  2. Run: streamlit run app.py
  3. Open: http://localhost:8501

If deploying to STREAMLIT CLOUD:
  1. Configure secrets in Streamlit Cloud → Settings → Secrets
  2. Git push to deploy
  3. Check app logs for errors

═══════════════════════════════════════════════════════════════════════════
""")

print("✅ Diagnostics complete!")
print("="*80)
