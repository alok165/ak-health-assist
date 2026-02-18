python -m venv venv
venv\Scripts\activate (On Windows) and source venv/bin/activate  (on Linux)
pip install -r requirements.txt

To check the packages that being installed:
python.exe -m pip list
#Allow powershell to have remotesigned in:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Set git profile to push:
git config --global user.email "alok165@gmail.com"
git config --global user.name "Alok Kumar"
git config --list

Create a git repos:
Initialize git (if you haven’t already):
##
git init
Add all files (your .gitignore will filter out venv, .env, etc.):

git add .
Commit:

git commit -m "Initial commit"
Set the main branch name:

git branch -M main
Add the GitHub remote:

git remote add origin https://github.com/alok165/my-agentic-ai.git
Push to GitHub:

git push -u origin main
Gradio is an open-source Python package that allows you to quickly build a demo or web application for your machine learning model, API, or any arbitrary Python function
pip install --upgrade gradio
pip install python-dotenv
pip install chromadb
To check the library and dependencies installed :
pip list 