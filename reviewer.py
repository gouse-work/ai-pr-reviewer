from langchain_groq import ChatGroq
from dotenv import load_dotenv
import json, os
import requests

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile")

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

# Files to ignore — reviewer script and config files
IGNORE_FILES = [
    "reviewer.py",
    ".env",
    ".gitignore",
    "reviewer_std.py",
    "reviewer_manual_diff.py"
]

def review_diff(diff: str) -> dict:
    response = llm.invoke(PROMPT.format(diff=diff))
    try:
        return json.loads(response.content)
    except:
        return {"comments": [], "summary": response.content}

def get_pr_diff(repo: str, pr_number: int, token: str) -> str:
    """Fetch only project files, ignoring reviewer/config files"""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"GitHub API error: {response.status_code}")

    files = response.json()

    diff = ""
    for file in files:
        if file["filename"] not in IGNORE_FILES:
            diff += f"\n--- {file['filename']} ---\n"
            diff += file.get("patch", "No changes")

    if not diff:
        diff = "No project files changed."

    return diff

def get_pr_info(repo: str, pr_number: int, token: str) -> dict:
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    headers = {"Authorization": f"Bearer {token}"}
    data = requests.get(url, headers=headers).json()
    return {
        "commit_id": data["head"]["sha"],
        "title": data["title"],
    }

def post_pr_comment(repo, pr_number, token, body):
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {"Authorization": f"Bearer {token}"}
    requests.post(url, headers=headers, json={"body": body})

def format_review_as_markdown(review: dict) -> str:
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

def run_review(repo, pr_number):
    token = os.getenv("GITHUB_TOKEN")
    print(f"Reviewing PR #{pr_number} in {repo}...")
    diff = get_pr_diff(repo, pr_number, token)
    review = review_diff(diff)
    comment = format_review_as_markdown(review)
    post_pr_comment(repo, pr_number, token, comment)
    print("✅ Review posted!")

if __name__ == "__main__":
    # In GitHub Actions, these are set automatically
    repo = os.getenv("REPO")           # e.g. "alice/ai-pr-reviewer"
    pr_number = os.getenv("PR_NUMBER")  # e.g. "42"
    
    if repo and pr_number:
        # Running in GitHub Actions
        run_review(repo, int(pr_number))
    else:
        # Running locally for testing
        run_review("YOUR_USERNAME/ai-pr-reviewer", 3)