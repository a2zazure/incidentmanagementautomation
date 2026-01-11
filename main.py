import requests
import json
import datetime

def main():
    # URL of the local Flask app's API
    url = "http://127.0.0.1:5001/api/incidents"

    try:
        # Fetch data from the URL
        response = requests.get(url)
        response.raise_for_status()

        # Parse JSON response
        data = response.json()
        incidents = data.get("incidents", [])

        output_file = "incidents.jsonl"
        with open(output_file, "w") as f:
            for inc in incidents:
                # Map fields to match specific schema requirements
                record = {
                    "id": f"INC-{inc.get('number', '000000'):06}",
                    "createdAt": inc.get('created_at'),
                    "title": inc.get('title'),
                    "tables": ["SecurityEvent", "Heartbeat"], # Hardcoded placeholder
                    "severity": "P2", # Hardcoded placeholder
                    "status": inc.get('status').lower()
                }
                
                # Write as single line JSON
                f.write(json.dumps(record) + "\n")
                
        print(f"Successfully exported {len(incidents)} incidents to {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON response")

if __name__ == "__main__":
    main()
