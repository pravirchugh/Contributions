from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# GitHub credentials
token = os.getenv("GITHUB_PAT")
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize FastAPI app
app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

class SummaryRequest(BaseModel):
    repo_owner: str
    repo_name: str
    username: str

@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("static/index.html", "r") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)

@app.post("/summarize_commits")
async def summarize_commits(request: SummaryRequest):
    commit_summaries = []  # stores main points of every commit
    detailed_commit_summaries = []  # stores detailed summaries from LLM
    seen_commits = set()  # don't process the same commit twice

    # GitHub API URL based on request data
    url = f"https://api.github.com/repos/{request.repo_owner}/{request.repo_name}/commits"

    # GitHub API headers
    github_headers = {'Authorization': f'token {token}'}

    # Fetch all commits by the specific user
    page = 1
    while True:
        params = {'per_page': 100, 'page': page}
        response = requests.get(url, headers=github_headers, params=params)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        commits = response.json()

        if not commits:
            break

        for commit in commits:
            commit_sha = commit['sha']

            # No duplicates
            if commit_sha in seen_commits:
                continue
            seen_commits.add(commit_sha)

            commit_author = commit['commit']['author']['name'] if commit['commit']['author'] else "Unknown"

            if commit_author.lower() != request.username.lower():
                continue

            # Check if this is a merge commit
            if len(commit['parents']) > 1:
                merge_commit_url = f"{url}/{commit_sha}"
                merge_commit_response = requests.get(merge_commit_url, headers=github_headers)

                if merge_commit_response.status_code != 200:
                    continue

                merge_commit_data = merge_commit_response.json()

                # Extract and summarize the diff introduced by the merge commit
                summary = f"Merge Commit: {commit_sha}\n"
                summary += f"Message: {merge_commit_data['commit']['message']}\n"
                summary += f"Date: {merge_commit_data['commit']['committer']['date']}\n"
                summary += "Merged branches and changes:\n"

                for file in merge_commit_data['files']:
                    file_changes = f"- {file['filename']}: +{file['additions']} / -{file['deletions']} ({file['status']})"
                    summary += file_changes + "\n"

                commit_summaries.append(summary)
                continue

            # Fetch detailed information for each non-merge commit
            commit_url = f"{url}/{commit_sha}"
            commit_response = requests.get(commit_url, headers=github_headers)

            if commit_response.status_code != 200:
                continue

            commit_data = commit_response.json()

            # Summarize the commit
            summary = f"Commit: {commit_sha}\n"
            summary += f"Message: {commit_data['commit']['message']}\n"
            summary += f"Date: {commit_data['commit']['committer']['date']}\n"
            summary += "Changes:\n"

            for file in commit_data['files']:
                file_changes = f"- {file['filename']}: +{file['additions']} / -{file['deletions']} ({file['status']})"
                summary += file_changes + "\n"

            commit_summaries.append(summary)

        page += 1

    # OpenAI API setup
    if openai_api_key is None:
        raise HTTPException(status_code=500, detail="OpenAI API key is invalid.")

    openai_url = "https://api.openai.com/v1/chat/completions"
    openai_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}"
    }

    # Generate a detailed summary for each commit summary
    for commit_summary in commit_summaries:
        data_detailed_summary = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": f"""
You are an AI assistant tasked with summarizing GitHub commit changes. Given the following commit information, generate a detailed paragraph summary, 100 words or less, that explains the specific changes and contributions made in this commit:

Input:

{commit_summary}

Output Format:

A 100 word or less detailed summary describing the changes and their impact.
"""
                }
            ]
        }

        response_detailed_summary = requests.post(openai_url, headers=openai_headers, json=data_detailed_summary)

        if response_detailed_summary.status_code == 200:
            detailed_summary = response_detailed_summary.json()['choices'][0]['message']['content']
            detailed_commit_summaries.append(detailed_summary)
        else:
            continue

    # Combine all detailed summaries into a single input for the final summary
    detailed_summaries_string = "\n".join(detailed_commit_summaries)

    # Generate a final summary in bullet points highlighting the main contributions
    data_final_summary = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": f"""
You are an AI designed to summarize commit histories and contributions in order to put on a Resume. Given the following detailed commit summaries, generate a final summary in four bullet points or less highlighting the main contributions:

Include specifics about important libraries, APIs, technologies, frameworks, languages used.

Input:

{detailed_summaries_string}

Output Format:

- Contribution 1: Description
- Contribution 2: Description
- Contribution 3: Description
- ...

Only output the final summary in bullet points.
"""
            }
        ]
    }

    response_final_summary = requests.post(openai_url, headers=openai_headers, json=data_final_summary)

    if response_final_summary.status_code == 200:
        final_summary = response_final_summary.json()['choices'][0]['message']['content']
        return JSONResponse(content={"final_summary": final_summary})
    else:
        raise HTTPException(status_code=response_final_summary.status_code, detail="Error generating final summary")

# Run the server using uvicorn
# Command: uvicorn main:app --reload
