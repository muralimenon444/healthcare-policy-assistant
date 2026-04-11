"""
Connection Test Script for Databricks SQL Warehouse
Run this locally before deploying to Streamlit Cloud
"""

import sys
from databricks import sql
import pandas as pd

def test_connection():
    """Test Databricks SQL Warehouse connection and data access."""
    
    print("="*70)
    print("DATABRICKS SQL WAREHOUSE CONNECTION TEST")
    print("="*70)
    
    # Step 1: Load credentials
    print("\n[1/5] Loading credentials from .streamlit/secrets.toml...")
    try:
        import toml
        secrets = toml.load(".streamlit/secrets.toml")
        
        host = secrets["DATABRICKS_HOST"]
        token = secrets["DATABRICKS_TOKEN"]
        warehouse_id = secrets["DATABRICKS_WAREHOUSE_ID"]
        
        print(f"   ✅ Host: {host}")
        print(f"   ✅ Token: {token[:10]}... (hidden)")
        print(f"   ✅ Warehouse ID: {warehouse_id}")
    except FileNotFoundError:
        print("   ❌ ERROR: .streamlit/secrets.toml not found")
        print("   Create this file with your Databricks credentials")
        return False
    except KeyError as e:
        print(f"   ❌ ERROR: Missing key in secrets: {e}")
        return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False
    
    # Step 2: Establish connection
    print("\n[2/5] Connecting to Databricks SQL Warehouse...")
    try:
        connection = sql.connect(
            server_hostname=host,
            http_path=f"/sql/1.0/warehouses/{warehouse_id}",
            access_token=token
        )
        print("   ✅ Connection established")
    except Exception as e:
        print(f"   ❌ CONNECTION FAILED: {e}")
        print("\n   Troubleshooting:")
        print("   • Check DATABRICKS_HOST format (no https://)")
        print("   • Verify token is valid and not expired")
        print("   • Ensure SQL Warehouse is running")
        print("   • Check WAREHOUSE_ID is correct")
        return False
    
    # Step 3: Test catalog access
    print("\n[3/5] Testing catalog access...")
    try:
        cursor = connection.cursor()
        cursor.execute("SHOW CATALOGS")
        catalogs = [row[0] for row in cursor.fetchall()]
        
        if "research_catalog" in catalogs:
            print("   ✅ research_catalog found")
        else:
            print("   ⚠️  WARNING: research_catalog not found")
            print(f"   Available catalogs: {catalogs}")
        
        cursor.close()
    except Exception as e:
        print(f"   ❌ CATALOG ACCESS FAILED: {e}")
        return False
    
    # Step 4: Test table access
    print("\n[4/5] Testing table access...")
    tables = {
        "graphrag_entities": "research_catalog.healthcare.graphrag_entities",
        "graphrag_relationships": "research_catalog.healthcare.graphrag_relationships",
        "graphrag_text_units": "research_catalog.healthcare.graphrag_text_units",
        "graphrag_common_qas": "research_catalog.healthcare.graphrag_common_qas"
    }
    
    table_results = {}
    
    for table_name, full_name in tables.items():
        try:
            cursor = connection.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {full_name}")
            count = cursor.fetchone()[0]
            table_results[table_name] = count
            print(f"   ✅ {table_name}: {count:,} records")
            cursor.close()
        except Exception as e:
            print(f"   ❌ {table_name}: ERROR - {str(e)[:50]}")
            table_results[table_name] = None
    
    # Step 5: Test query execution
    print("\n[5/5] Testing sample query...")
    try:
        cursor = connection.cursor()
        query = f"""
        SELECT text, type 
        FROM {tables['graphrag_entities']} 
        LIMIT 5
        """
        cursor.execute(query)
        results = cursor.fetchall()
        
        print(f"   ✅ Query executed successfully")
        print(f"   Sample entities:")
        for i, row in enumerate(results, 1):
            print(f"      {i}. {row[0]} ({row[1]})")
        
        cursor.close()
    except Exception as e:
        print(f"   ❌ QUERY FAILED: {e}")
        connection.close()
        return False
    
    # Close connection
    connection.close()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    all_good = all(v is not None and v > 0 for v in table_results.values())
    
    if all_good:
        print("\n✅ ALL TESTS PASSED!")
        print("\nYou are ready to deploy to Streamlit Cloud.")
        print("\nNext steps:")
        print("   1. Push code to GitHub")
        print("   2. Configure secrets in Streamlit Cloud")
        print("   3. Deploy app")
        return True
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("\nIssues found:")
        for table_name, count in table_results.items():
            if count is None:
                print(f"   ❌ {table_name}: Table not accessible")
            elif count == 0:
                print(f"   ⚠️  {table_name}: Table is empty")
        
        print("\nPlease fix these issues before deploying.")
        print("\nTroubleshooting:")
        print("   • Run setup_delta_tables.sql to create tables")
        print("   • Run migrate_to_v3.4.ipynb to populate data")
        print("   • Grant SELECT permissions to your user/token")
        return False

if __name__ == "__main__":
    # Check dependencies
    try:
        import toml
    except ImportError:
        print("ERROR: toml package not installed")
        print("Install with: pip install toml")
        sys.exit(1)
    
    try:
        from databricks import sql
    except ImportError:
        print("ERROR: databricks-sql-connector not installed")
        print("Install with: pip install databricks-sql-connector")
        sys.exit(1)
    
    # Run test
    success = test_connection()
    
    sys.exit(0 if success else 1)
