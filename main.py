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

        output_file = "incidents.txt"
        with open(output_file, "w") as f:
            header = f"{'No.':<8} {'Created On':<22} {'Status':<12} {'Details'}"
            f.write(header + "\n")
            f.write("-" * 80 + "\n")

            for inc in incidents:
                number = inc.get('number')
                created_at = inc.get('created_at')
                status = inc.get('status')
                details = inc.get('title') # Mapping 'title' to 'Details'

                line = f"{number:<8} {created_at:<22} {status:<12} {details}"
                f.write(line + "\n")
                
        print(f"Successfully exported {len(incidents)} incidents to {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON response")

if __name__ == "__main__":
    main()
