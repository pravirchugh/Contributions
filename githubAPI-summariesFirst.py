import requests
import os
from dotenv import load_dotenv

load_dotenv()

# GitHub credentials
token = os.getenv("GITHUB_PAT")
repo_owner = 'pravirchugh'
repo_name = 'UpVoice'
username = 'pravirchugh'

# API endpoint for commit retrieval
url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits"

headers = {'Authorization': f'token {token}'}

commit_summaries = [] # stores main points of every commit
detailed_commit_summaries = []  # stores detailed summaries from LLM

seen_commits = set() # don't process same commit twice

page = 1
while True:
    params = {'per_page': 100, 'page': page}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"Error fetching commits: {response.status_code} {response.text}")
        break

    commits = response.json()

    if not commits:
        print(f"No more commits found on page {page}.")
        break

    print(f"Page {page} - Number of commits retrieved: {len(commits)}")

    for commit in commits:
        commit_sha = commit['sha']

        # No duplicates
        if commit_sha in seen_commits:
            continue
        seen_commits.add(commit_sha)

        commit_author = commit['commit']['author']['name'] if commit['commit']['author'] else "Unknown"
        commit_email = commit['commit']['author']['email'] if commit['commit']['author'] else "Unknown"

        print(f"Processing commit {commit_sha} by {commit_author} ({commit_email})")

        if commit_author.lower() != username.lower():
            print(f"Skipping commit {commit_sha} by {commit_author} since it doesn't match the author filter.")
            continue

        # Check if this is a merge commit
        if len(commit['parents']) > 1:
            merge_commit_url = f"{url}/{commit_sha}"
            merge_commit_response = requests.get(merge_commit_url, headers=headers)

            if merge_commit_response.status_code != 200:
                print(f"Failed to retrieve merge commit details for {commit_sha}: {merge_commit_response.status_code}")
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
        commit_response = requests.get(commit_url, headers=headers)

        if commit_response.status_code != 200:
            print(f"Failed to retrieve commit details for {commit_sha}: {commit_response.status_code}")
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
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key is None:
    print("OPENAI API KEY Invalid.")
    exit()

url = "https://api.openai.com/v1/chat/completions"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {openai_api_key}"
}

# Generate a detailed summary for each commit summary
    # The commit summary stores the specific code changed. The detailed summary is the individual commit summary.
    # Need to take all of those summaries and merge them into four bullet points.
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

An 100 word or less detailed summary describing the changes and their impact.
"""
            }
        ]
    }

    response_detailed_summary = requests.post(url, headers=headers, json=data_detailed_summary)

    if response_detailed_summary.status_code == 200:
        detailed_summary = response_detailed_summary.json()['choices'][0]['message']['content']
        detailed_commit_summaries.append(detailed_summary)
        print(f"Detailed Summary for Commit: {detailed_summary}\n")
    else:
        print(f"Error generating detailed summary for commit: {response_detailed_summary.status_code}, {response_detailed_summary.text}")

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

response_final_summary = requests.post(url, headers=headers, json=data_final_summary)

if response_final_summary.status_code == 200:
    print("Final Summary of Contributions:")
    print(response_final_summary.json()['choices'][0]['message']['content'])
else:
    print("Error generating final summary:", response_final_summary.status_code, response_final_summary.text)
