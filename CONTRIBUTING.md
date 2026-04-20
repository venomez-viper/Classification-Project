# Contributing Guide
MGT 599 Capstone - Group 4

This document explains how the team should work with this repository to avoid overwriting each other's work.

## Branch Strategy

Each team member works on their own branch. Do not commit directly to main.

Create your branch the first time you clone the repo:

```
git checkout -b member1-lead
```

Use your role as the branch name, for example:
- member1-lead
- member2-dashboard
- member3-task1
- member4-task2
- member5-modelready

Stay on your branch for all your work. Only the team lead merges into main.

## Starting a Work Session

Before you start working, always pull the latest version of main so you have the most recent changes:

```
git checkout main
git pull origin main
git checkout your-branch-name
git merge main
```

This keeps your branch up to date and reduces merge conflicts.

## File Ownership

Each person is responsible for one script. Do not edit another person's script without telling them first.

- lead_tracking.py - Member 1
- dashboard.py - Member 2
- task1_features.py - Member 3
- task2_features.py - Member 4
- model_ready.py - Member 5

If you need to change something in common_utils.py, tell the team first since everyone depends on it.

## Commit Message Rules

Every commit message should say what you did and which file it affected. Write in past tense, keep it under 72 characters.

Good examples:
```
task1 features - added tfidf on combined text columns
dashboard - fixed missing value chart label
model ready - dropped near-constant columns from task2
```

Bad examples:
```
updated stuff
fixed bug
changes
```

Do not commit broken code. If you are in the middle of something and need to save your progress, add a note in the message:

```
task1 features - wip, tfidf not wired up yet
```

## How to Submit Your Work

When your section is done and you want it reviewed before it goes into main:

```
git add scripts/your_script.py
git commit -m "your message here"
git push origin your-branch-name
```

Then open a Pull Request on GitHub from your branch into main. The team lead reviews it and merges.

If you have never done a pull request: go to the repo on GitHub, click the "Compare and pull request" button that appears after you push, write a short description of what you did, and submit.

## What Not to Commit

- Raw data files (data/raw/)
- DuckDB files (data/db/)
- Cleaned CSV outputs (data/cleaned/)
- Any file in outputs/
- Jupyter notebook checkpoint folders (.ipynb_checkpoints/)
- Temporary Word or Excel files (starting with ~$)

The .gitignore file already handles most of these but double-check with git status before committing.

## Handling Conflicts

If you get a merge conflict when pulling main into your branch:

1. Open the conflicted file in VS Code
2. Git will mark the conflict with <<<<<<, =======, and >>>>>>>
3. Keep the version that is correct, delete the markers
4. Save the file, then run:

```
git add the-conflicted-file.py
git commit -m "resolved merge conflict in filename"
```

If you are unsure which version to keep, do not guess. Contact the team lead.

## End of Week Checklist

Before the weekly deadline, make sure you have done the following:

- Your script runs without errors from top to bottom
- Your output files are saved in the correct outputs/ folder
- You have filled in a handoff note in docs/handoff_notes/
- Your changes are pushed to your branch and a pull request is open
