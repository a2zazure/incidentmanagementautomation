
import os
import json
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

client = AzureOpenAI(
    api_key=os.environ.get("AZURE_MODEL_KEY"),
    api_version="2024-05-01-preview",
    azure_endpoint="https://samratisbest-4230-resource.cognitiveservices.azure.com/"
)

def analyze_incidents():
    input_file = "incidents.jsonl"
    missing_data_tables = []
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    print("Analyzing incidents with AI agent...")
    
    with open(input_file, 'r') as f:
        lines = f.readlines()
        
    for line in lines:
        try:
            incident = json.loads(line)
            # Use 'title' as the description since that's where the alert text is
            description = incident.get('title', '')
            
            if not description:
                continue
                
            response = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an incident triage assistant. Check if the incident description indicates that a specific table 'does not get data for last 3 months'. If it matches this pattern, extract and return ONLY the table name (e.g. 'AzureMetrics'). If it does not match this pattern, return 'None'."
                    },
                    {
                        "role": "user",
                        "content": f"Incident: {description}"
                    }
                ],
                model="gpt-4.1",
                temperature=0,
            )
            
            result = response.choices[0].message.content.strip()
            
            if result and result != 'None':
                print(f"Found missing data table: {result} for Incident: {incident.get('id')}")
                # Store both the table name and the incident ID
                missing_data_tables.append({
                    "table": result,
                    "id": incident.get('id', '').replace('INC-', '').lstrip('0') # Extract clean number for API
                })
                
        except json.JSONDecodeError:
            continue
        except Exception as e:
            print(f"Error processing incident: {e}")

    print("\nSummary of tables with missing data:")
    # Print just unique tables for cleaner output
    unique_tables = list(set([item['table'] for item in missing_data_tables]))
    print(unique_tables)
    
    return missing_data_tables

if __name__ == "__main__":
    analyze_incidents()
