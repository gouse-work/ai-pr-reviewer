from langchain_groq import ChatGroq
from dotenv import load_dotenv
import json, os
import requests

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

def get_pr_diff(repo: str, pr_number: int, token: str) -> str:
    """
    Fetch the code diff from a GitHub Pull Request.
    
    repo = "username/repo-name"  e.g. "alice/my-project"
    pr_number = the PR number  e.g. 42
    token = your GitHub token
    """
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"Bearer {token}",
        # This magic header tells GitHub to return the diff format
        "Accept": "application/vnd.github.v3.diff"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.text  # The actual diff text
    else:
        raise Exception(f"GitHub API error: {response.status_code}")

def get_pr_info(repo: str, pr_number: int, token: str) -> dict:
    """Get PR metadata (commit ID, file paths) needed to post comments"""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    headers = {"Authorization": f"Bearer {token}",
               "Accept": "application/vnd.github.v3.diff"}
    data = requests.get(url, headers=headers).json()
    return {
        "commit_id": data["head"]["sha"],   # Latest commit hash
        "title": data["title"],               # PR title
    }
def post_pr_comment(repo, pr_number, token, body):
    """Post a general comment on the PR (simpler than inline comments)"""
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {"Authorization": f"Bearer {token}",
               "Accept": "application/vnd.github.v3.diff"}
    requests.post(url, headers=headers, json={"body": body})

def format_review_as_markdown(review: dict) -> str:
    """Convert AI's JSON response into a pretty markdown comment"""
    md = "## 🤖 AI Code Review\n\n"
    md += f"**Summary:** {review.get('summary', 'Review complete.')}\n\n"
    
    severity_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    
    for comment in review.get("comments", []):
        icon = severity_icons.get(comment.get("severity", "low"), "ℹ️")
        md += f"{icon} **Line {comment['line']}:** {comment['message']}\n"
        if comment.get("suggestion"):
            md += f"   > 💡 Suggestion: `{comment['suggestion']}`\n"
        md += "\n"
    
    return md

# FULL FLOW — ties everything together
def run_review(repo, pr_number):
    token = os.getenv("GITHUB_TOKEN")
    
    print(f"Reviewing PR #{pr_number} in {repo}...")
    diff = get_pr_diff(repo, pr_number, token)
    review = review_diff(diff)
    comment = format_review_as_markdown(review)
    post_pr_comment(repo, pr_number, token, comment)
    print("✅ Review posted!")

run_review("gouse-work/ai-pr-reviewer",2)