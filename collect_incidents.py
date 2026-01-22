import requests
import json
import datetime

def main():
    # URL of the local Flask app's API with agent format
    url = "http://127.0.0.1:5001/api/incidents?format=agent"

    try:
        # Fetch data from the URL
        response = requests.get(url)
        response.raise_for_status()

        # Parse JSON response
        data = response.json()
        incidents = data.get("incidents", [])

        output_file = "incidents.jsonl"
        with open(output_file, "w") as f:
            count = 0
            for inc in incidents:
                # Filter for Open incidents (Triggered or Acknowledged)
                current_status = inc.get('status').lower()
                if current_status not in ['triggered', 'acknowledged']:
                    continue

                # API already provides the correct schema
                f.write(json.dumps(inc) + "\n")
                count += 1
                
        print(f"Successfully exported {count} open incidents to {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON response")

if __name__ == "__main__":
    main()
