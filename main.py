print("Main script starting...", flush=True)
import collect_incidents
import triage
import verify_tables
import time
import requests
import json

def resolve_incidents(incident_ids):
    if not incident_ids:
        return
        
    url = "http://127.0.0.1:5001/api/incidents/bulk_update"
    payload = {
        "action": "resolve",
        "incident_ids": incident_ids
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f" Successfully resolved {len(incident_ids)} incidents: {incident_ids}")
    except Exception as e:
        print(f"Failed to verify/resolve incidents: {e}")

def run_pipeline():
    print(" Starting Incident Management Pipeline")
    print("=" * 50)
    
    # Step 1: Collect Incidents
    print("\n[Step 1] Collecting incidents...")
    collect_incidents.main()
    print("Collection complete.")
    
    # Step 2: AI Triage
    print("\n[Step 2] Running AI Triage...")
    # Triage now returns detailed list: [{'table': 'Usage', 'id': '32508'}, ...]
    triage_results = triage.analyze_incidents()
    
    if not triage_results:
        print("No tables needing verification found. Pipeline finished.")
        return
        
    unique_tables_to_verify = list(set([item['table'] for item in triage_results]))
    print(f"Triage complete. Tables to check: {unique_tables_to_verify}")
    
    # Step 3: Verify Data
    print("\n[Step 3] Verifying Data in Azure...")
    verified_tables, detailed_logs = verify_tables.verify_table_data(unique_tables_to_verify)
    print(f"Verification complete. verified_tables: {verified_tables}")
    
    # Save logs to file
    log_file = "verification_logs.json"
    try:
        with open(log_file, "w") as f:
            json.dump(detailed_logs, f, indent=2)
        print(f"Detailed logs saved to {log_file}")
    except Exception as e:
        print(f"Error saving logs: {e}")

    # Step 4: Auto-Resolve
    if verified_tables:
        print("\n[Step 4] Auto-Resolving Verified Incidents...")
        incidents_to_resolve = []
        
        for item in triage_results:
            if item['table'] in verified_tables and item['id']:
                 incidents_to_resolve.append(item['id'])
        
        if incidents_to_resolve:
            resolve_incidents(list(set(incidents_to_resolve)))
        else:
            print("ℹNo incidents matched the verified tables.")
    else:
        print("\nℹNo tables were verified as having data. No incidents to resolve.")

    # Step 5: AI Summary
    print("\n[Step 5] Generating AI Summary Report...")
    import summarize_logs
    summary_text = summarize_logs.generate_summary(log_file)
    
    print("\n" + "-"*30)
    print("SUMMARY REPORT")
    print("-"*30)
    print(summary_text)
    print("-"*30)
    
    with open("resolution_summary.txt", "w") as f:
        f.write(summary_text)
    print("Summary saved to resolution_summary.txt")

    print("\n" + "=" * 50)
    print("Pipeline Execution Finished")

if __name__ == "__main__":
    run_pipeline()
