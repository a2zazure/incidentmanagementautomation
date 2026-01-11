
import os
import sys
from azure.identity import DefaultAzureCredential
from azure.monitor.query import LogsQueryClient, LogsQueryStatus
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def verify_table_data(tables):
    credential = DefaultAzureCredential()
    client = LogsQueryClient(credential)
    workspace_id = os.environ.get("LOG_ANALYTICS_WORKSPACE_ID")

    if not workspace_id:
        print("Error: LOG_ANALYTICS_WORKSPACE_ID environment variable is not set.")
        return

    print(f"Checking data existence for tables: {', '.join(tables)} (Last 90 days)")

    for table in tables:
        query = f"{table} | where TimeGenerated > ago(90d) | take 1"
        
        try:
            response = client.query_workspace(
                workspace_id=workspace_id,
                query=query,
                timespan=timedelta(days=90)
            )

            if response.status == LogsQueryStatus.SUCCESS:
                if response.tables and len(response.tables[0].rows) > 0:
                    print(f"✅ Data found for {table}")
                else:
                    print(f"❌ No data found for {table}")
            else:
                print(f"⚠️ Query failed for {table}: {response}")
                
        except Exception as e:
             print(f"⚠️ Error querying {table}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_tables.py <table1> <table2> ...")
        # Default to the tables we know about for convenience if run without args
        default_tables = ['AzureMetrics', 'Usage']
        print(f"No tables provided, checking default list: {default_tables}")
        verify_table_data(default_tables)
    else:
        verify_table_data(sys.argv[1:])
