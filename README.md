# 📚 Flask Library Management System

## Setup Guide

### Step 1: Install requirements
```bash
pip install flask
```

### Step 2: Navigate to the Project Folder
```bash
cd library_app
```

### Step 3: Run the Application
```bash
python app.py
```

### Step 4: Open in Your Browser
```
http://127.0.0.1:5000
```

---

## Features

| Page | URL | Description |
|------|-----|---------------|
| Dashboard | `/` | Stats + recent activity |
| Books | `/books` | Sabhi books, search, filter |
| Book Add | `/books/add` | add new book |
| Members | `/members` | Registered members |
|Add member | `/members/add` | Register a new member |
| Issue Book | `/issue` | Issue a book to a member |
| Return Book | `/return` |Return an issued book |
| Records | `/records` | View complete issue and return history |

## Database
Uses SQLite (library.db)
Database is created automatically on first run
Sample books and members are loaded automatically

## Project Structure
```
library_app/
├── app.py              ← Main Flask app
├── requirements.txt    ← Dependencies
├── library.db          ← SQLite database (auto-generated)
└── templates/
    ├── base.html       ← Common layout
    ├── index.html      ← Dashboard
    ├── books.html      ← Books list
    ├── add_book.html   ← Add book form
    ├── members.html    ← Members list
    ├── add_member.html ← Add member form
    ├── issue.html      ← Issue book
    ├── return.html     ← Return book
    └── records.html    ← All records
```
