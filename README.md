# GitHub Commit Summarizer

## What the App Does

The **Contribution Summarizer** is a web application that generates concise summaries of a user's GitHub commit history to a specific repository. By entering the repository owner, repository name, and GitHub username, the app provides an LLM-generated summary of the user's contributions, which can be useful for resumes or project documentation.

## How to Start the App

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/pravirchugh/Contributions-Summarizer.git
   cd repository-name
   ```
2. **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3. **Add GitHub and OpenAI API Credentials**:
    You will need an OpenAI API Key and a GitHub Personal Access Token to use this repository.
    Create a .env file in the project directory and add the following credentials:
    ```html
    OPENAI_API_KEY=<Your OpenAI API Key>
    GITHUB_PAT=<Your GitHub Personal Access Token>
    ```

4. **Run the Application**:
    ```bash
    uvicorn main:app --reload
    ```
5. **Access the Application**: 
    Open your web browser and go to http://127.0.0.1:8000 to use the application.
