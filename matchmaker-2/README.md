# Matchmaker Tool

A simple tool for storing and analyzing dossiers using Google's Gemini API.

## Setup

1. Create a `.env` file in the root directory with your Gemini API key:
```
GEMINI_API_KEY=your_api_key_here
```

2. Install dependencies:
```
pip install -r requirements.txt
```

## Usage

### Managing Dossiers
- Store dossiers as text files in the `dossiers` folder
- Each dossier should be a text file named `[person_name].txt`
- You can include any information you want in the dossier

### Using the Tool
Run the main script:
```
py matchmaker.py
```

The script will help you:
- Create new dossiers
- Query Gemini about dossiers
- Extract information from files to add to dossiers

## Example Commands
- "Create a new dossier for John"
- "Find someone with similar religious views to Sarah"
- "Analyze tweets.txt and add insights to John's dossier" 