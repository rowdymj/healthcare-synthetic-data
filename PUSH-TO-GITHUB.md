# Push This Project to GitHub

Step-by-step instructions. Run these in Terminal (Mac) or Command Prompt (Windows).

---

## One-time setup (skip if you've done this before)

### 1. Install the GitHub CLI

Mac (with Homebrew):
```bash
brew install gh
```

Windows: download from https://cli.github.com

### 2. Log in to GitHub

```bash
gh auth login
```

It will ask you a few questions — pick these:
- **GitHub.com** (not Enterprise)
- **HTTPS**
- **Login with a web browser**

It'll give you a code, open your browser, and you paste the code in. Done.

---

## Push the project

### 3. Open Terminal and go to the project folder

```bash
cd /path/to/healthcare-synthetic-data
```

Replace `/path/to/` with wherever the folder actually is on your computer.

### 4. Initialize Git (first time only)

```bash
git init
```

### 5. Stage all files

```bash
git add -A
```

This tells Git "I want to track everything in this folder." The `.gitignore` file will automatically skip things like `__pycache__` and `.DS_Store`.

### 6. Create your first commit

```bash
git commit -m "Initial commit: healthcare agent sandbox"
```

### 7. Create the GitHub repo and push

For a **private** repo (recommended — keeps your data private):
```bash
gh repo create healthcare-synthetic-data --private --source=. --push
```

For a **public** repo:
```bash
gh repo create healthcare-synthetic-data --public --source=. --push
```

That's it. The `gh repo create` command does three things at once: creates the repo on GitHub, links your local folder to it, and pushes all your code up.

### 8. Verify it worked

```bash
gh repo view --web
```

This opens the repo in your browser so you can see everything landed.

---

## Sharing with your team

Once the repo exists, share the URL with your engineers:

```
https://github.com/YOUR-USERNAME/healthcare-synthetic-data
```

They clone it with:
```bash
git clone https://github.com/YOUR-USERNAME/healthcare-synthetic-data.git
cd healthcare-synthetic-data
```

Then follow the README to get running.

---

## Making changes later

After you edit files and want to push updates:

```bash
git add -A
git commit -m "Describe what you changed"
git push
```

That's the whole workflow: add, commit, push. Three commands.
