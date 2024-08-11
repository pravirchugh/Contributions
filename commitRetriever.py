import git
import os
import shutil



repo_url = "https://github.com/pravirchugh/UpVoice.git"
repo_name = "UpVoice"
repo_clone_dir = "./clones/" + repo_name
username = "pravirchugh"

if os.path.exists(repo_clone_dir):
    shutil.rmtree(repo_clone_dir)
    os.makedirs(repo_clone_dir)

git.Repo.clone_from(repo_url, repo_clone_dir)

repo = git.Repo(repo_clone_dir)

# Get the list of all commits
commits = list(repo.iter_commits())

# Filter commits by author name (username)
user_commits = [commit for commit in commits if commit.author.name == username]

print(user_commits)