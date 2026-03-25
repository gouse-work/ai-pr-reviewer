from langchain_groq import ChatGroq
from dotenv import load_dotenv
import json, os

# Load your API keys from the .env file
load_dotenv()

# Create an AI "brain" using Groq's fast model
llm = ChatGroq(model="llama-3.3-70b-versatile")

# This is the instruction we give the AI
# Think of it like briefing a junior developer
PROMPT = """
You are an expert code reviewer. Review this code diff carefully.
Check for: bugs, security issues, performance problems, style issues.

IMPORTANT: Respond ONLY with valid JSON in this exact format:
{{
  "comments": [
    {{
      "line": 5,
      "severity": "high",
      "message": "What the issue is",
      "suggestion": "How to fix it"
    }}
  ],
  "summary": "Overall review in 1-2 sentences"
}}

Diff to review:
{diff}
"""

def review_diff(diff: str) -> dict:
    """Send a diff to AI, get back review comments"""
    # Format the prompt with actual diff content
    response = llm.invoke(PROMPT.format(diff=diff))
    
    try:
        # Parse AI's response as JSON
        return json.loads(response.content)
    except:
        # If AI didn't return valid JSON, return as plain text
        return {"comments": [], "summary": response.content}

# TEST IT: Paste a sample diff here to try it out
if __name__ == "__main__":
    sample_diff = """
+def get_user(id):
+    password = "admin123"  # hardcoded secret!
+    query = f"SELECT * FROM users WHERE id = {id}"  # SQL injection!
+    return db.execute(query)
"""
    
    result = review_diff(sample_diff)
    print(json.dumps(result, indent=2))