import os
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Debug prints
api_key = os.getenv('GEMINI_API_KEY')
print(f"API Key loaded: {'Yes' if api_key else 'No'}")
print(f"API Key length: {len(api_key) if api_key else 0}")

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel('models/gemini-2.0-flash')

def ensure_dossiers_folder():
    """Create dossiers/male and dossiers/female folders if they don't exist."""
    Path('dossiers/male').mkdir(parents=True, exist_ok=True)
    Path('dossiers/female').mkdir(parents=True, exist_ok=True)
    Path('prompts').mkdir(exist_ok=True)

def get_dossier_path(name, sex):
    """Get the path for a dossier based on name and sex."""
    sex = sex.lower()
    if sex not in ['male', 'female']:
        raise ValueError("Sex must be 'male' or 'female'")
    return Path('dossiers') / sex / f"{name}.txt"

def list_available_prompts():
    """List all available prompt files in the prompts directory."""
    prompt_dir = Path('prompts')
    if not prompt_dir.exists():
        return []
    return [f.name for f in prompt_dir.glob('*.txt')]

def read_prompt_file(prompt_name):
    """Read the contents of a prompt file."""
    prompt_path = Path('prompts') / prompt_name
    if not prompt_path.exists():
        return None
    return prompt_path.read_text()

def create_dossier(name, sex):
    """Create a new dossier in the correct folder with the standard template."""
    ensure_dossiers_folder()
    file_path = get_dossier_path(name, sex)
    if file_path.exists():
        print(f"Dossier for {name} ({sex}) already exists.")
        return
    
    try:
        with open('dossier_template.txt', 'r') as f:
            template = f.read()
    except FileNotFoundError:
        print("Warning: dossier_template.txt not found. Creating empty dossier.")
        template = ""
    
    with file_path.open('w') as f:
        f.write(template)
    print(f"Created new dossier for {name} ({sex}) with template")

def read_dossier(name, sex):
    """Read the contents of a dossier."""
    file_path = get_dossier_path(name, sex)
    if not file_path.exists():
        return None
    return file_path.read_text()

def append_to_dossier(name, sex, content):
    """Append content to a dossier."""
    file_path = get_dossier_path(name, sex)
    with file_path.open('a') as f:
        f.write(f"\n{content}")

def query_gemini(prompt, context_dossiers=None, prompt_file=None):
    """Query Gemini with optional dossier context and prompt file. 
    context_dossiers is a list of (name, sex) tuples."""
    context = ""
    if context_dossiers:
        for name, sex in context_dossiers:
            content = read_dossier(name, sex)
            if content:
                context += f"\nDossier for {name} ({sex}):\n{content}\n"
    
    # If a prompt file is specified, read and use it
    if prompt_file:
        prompt_content = read_prompt_file(prompt_file)
        if prompt_content:
            prompt = prompt_content
    
    full_prompt = f"{context}\n\n{prompt}" if context else prompt
    
    response = model.generate_content(full_prompt)
    return response.text

def analyze_file_for_dossier(file_path, target_name, target_sex):
    """Analyze a file and add insights to a dossier."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        prompt = f"""Analyze the following content and extract key insights about the person's preferences, \
        personality traits, and interests. Format the output as clear, concise bullet points:\n\n        {content}"""
        
        insights = query_gemini(prompt)
        append_to_dossier(target_name, target_sex, f"\nInsights from {file_path}:\n{insights}")
        print(f"Added insights to {target_name}'s dossier")
    except FileNotFoundError:
        print(f"File {file_path} not found")

def prompt_for_sex():
    while True:
        sex = input("Enter sex (male/female): ").strip().lower()
        if sex in ['male', 'female']:
            return sex
        print("Invalid input. Please enter 'male' or 'female'.")

def select_prompt_file():
    """Let the user select a prompt file from available options."""
    prompts = list_available_prompts()
    if not prompts:
        print("No prompt files found in the prompts directory.")
        return None
    
    print("\nAvailable prompt files:")
    for i, prompt in enumerate(prompts, 1):
        print(f"{i}. {prompt}")
    
    while True:
        try:
            choice = int(input("\nSelect a prompt file (number) or 0 for none: "))
            if choice == 0:
                return None
            if 1 <= choice <= len(prompts):
                return prompts[choice - 1]
            print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a number.")

def main():
    ensure_dossiers_folder()
    
    while True:
        print("\nMatchmaker Tool")
        print("1. Create new dossier")
        print("2. Query Gemini about dossiers")
        print("3. Analyze file for dossier")
        print("4. Exit")
        
        choice = input("\nChoose an option (1-4): ")
        
        if choice == "1":
            name = input("Enter person's name: ")
            sex = prompt_for_sex()
            create_dossier(name, sex)
            
        elif choice == "2":
            prompt = input("Enter your query: ")
            context_entries = []
            while True:
                add = input("Add a dossier to context? (y/n): ").strip().lower()
                if add == 'y':
                    name = input("Enter dossier name: ")
                    sex = prompt_for_sex()
                    context_entries.append((name, sex))
                else:
                    break
            
            # Add prompt file selection
            prompt_file = select_prompt_file()
            
            response = query_gemini(prompt, context_entries if context_entries else None, prompt_file)
            print("\nGemini's response:")
            print(response)
            
        elif choice == "3":
            file_path = input("Enter path to file to analyze: ")
            target_name = input("Enter name of dossier to update: ")
            target_sex = prompt_for_sex()
            analyze_file_for_dossier(file_path, target_name, target_sex)
            
        elif choice == "4":
            break
        
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main() 