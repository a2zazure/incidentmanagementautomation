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

def generate_summary(log_file_path):
    if not os.path.exists(log_file_path):
        return "Error: Log file not found."
        
    with open(log_file_path, 'r') as f:
        try:
            logs = json.load(f)
        except json.JSONDecodeError:
            return "Error: Invalid JSON log file."

    if not logs:
        return "No logs to summarize."

    # Prepare prompt
    prompt = f"""
    You are an Incident Reporting Assistant. 
    Analyze the following verification logs from an automated incident resolution pipeline.
    
    Logs:
    {json.dumps(logs, indent=2)}
    
    Task:
    Create a concise and professional summary for an email to the operations team.
    
    Requirements:
    1. Start with a high-level status (e.g. "Incident Verification Report").
    2. List tables where data was successfully VERIFIED (Status: Verified).
    3. Highlight critical failures where data is MISSING or ERRORS occurred.
    4. For missing/error items, include the specific error message provided in the logs.
    5. Keep it clear and actionable.
    """

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant for IT operations."},
                {"role": "user", "content": prompt}
            ],
            model="gpt-4.1",
            temperature=0.3,
        )
        
        summary = response.choices[0].message.content.strip()
        return summary
        
    except Exception as e:
        return f"Error generating summary: {str(e)}"

if __name__ == "__main__":
    # Test with a dummy file if run directly
    test_file = "verification_logs.json"
    if os.path.exists(test_file):
        print(generate_summary(test_file))
    else:
        print(f"File {test_file} not found. Run main pipeline to generate it.")
