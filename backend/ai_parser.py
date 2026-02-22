import google.generativeai as genai
import PyPDF2
import json
import re
import os
from dotenv import load_dotenv

# 1. Load the hidden environment variables from your .env file
load_dotenv()

# 2. Securely fetch the API key
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ ERROR: API Key not found. Please check your .env file.")

# Configure the AI securely
genai.configure(api_key=api_key)

def extract_skills_from_pdf(filepath):
    print("\n" + "="*50)
    print("🚀 STARTING SECURE AI RESUME ANALYSIS...")
    print("="*50)

    raw_text = ""
    try:
        with open(filepath, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    raw_text += text
        print(f"✅ PDF read successfully. Found {len(raw_text)} characters.")
    except Exception as e:
        print(f"❌ PDF Error: {e}")
        return {}

    if not raw_text.strip():
        print("❌ Error: PDF text is empty.")
        return {}

    prompt = f"""
    Extract technical skills from this resume.
    Estimate proficiency from 1 to 3.
    Return ONLY valid JSON:

    {{
        "skills": {{
            "Python": 2,
            "SQL": 3
        }}
    }}

    Resume:
    {raw_text}
    """

    try:
        print("⏳ Waiting for Gemini AI...")
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)

        clean_text = response.text.strip()
        match = re.search(r'\{.*\}', clean_text, re.DOTALL)
        
        if match:
            json_string = match.group(0)
            parsed_data = json.loads(json_string)
            extracted_skills = parsed_data.get("skills", {})
            print(f"✅ AI Successfully Found: {extracted_skills}")
            return extracted_skills
        else:
            print("❌ AI returned invalid JSON.")
            return {}

    except Exception as e:
        print("❌ AI Error:", e)
        return {}
def generate_dynamic_job_requirements(target_job_title):
    """
    Asks Gemini to generate industry-standard required skills and weights 
    for ANY job title the user inputs.
    """
    print(f"\n⏳ Generating industry standards for: {target_job_title}...")
    
    prompt = f"""
    You are an expert HR recruiter. Define the top 5 most critical technical skills 
    required for the role of "{target_job_title}". 
    
    IMPORTANT RULE: Keep skill names very short and standardized. 
    Use "Excel" instead of "Advanced Microsoft Excel". 
    Use "SQL" instead of "SQL (Structured Query Language)".
    
    Assign a required proficiency (1 to 3) and an importance weight (1 to 3).
    1 = Beginner/Nice to have, 2 = Intermediate/Important, 3 = Expert/Mandatory.

    Return ONLY a valid JSON object in this exact format:
    {{
        "{target_job_title}": {{
            "Skill Name 1": {{"req_prof": 3, "weight": 3}},
            "Skill Name 2": {{"req_prof": 2, "weight": 2}}
        }}
    }}
    """

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)

        clean_text = response.text.strip()
        match = re.search(r'\{.*\}', clean_text, re.DOTALL)
        
        if match:
            json_string = match.group(0)
            parsed_data = json.loads(json_string)
            print(f"✅ Generated Requirements for {target_job_title}: {parsed_data}")
            return parsed_data
        else:
            return {}
    except Exception as e:
        print(f"❌ Error generating job requirements: {e}")
        return {}
def suggest_government_schemes(target_job, missing_skills):
    """
    Asks Gemini to find real Indian government schemes or portals
    based on the exact skills the user is missing.
    """
    print(f"\n⏳ AI is hunting for Indian Govt Schemes for {target_job}...")
    
    if not missing_skills:
        return []

    # Convert the list of missing skills into a comma-separated string for the AI
    skills_str = ", ".join(missing_skills)

    prompt = f"""
    You are an expert career counselor in India.
    A student is aiming for the role of "{target_job}" and needs to learn the following skills: {skills_str}.
    
    Suggest 3 to 4 real, official Indian government upskilling schemes, educational portals, or certifications (such as PMKVY, SWAYAM, NPTEL, Skill India Digital, or specific Sector Skill Councils) where they can learn these exact skills.

    Return ONLY a valid JSON array in this exact format:
    [
        {{
            "name": "Name of the Scheme or Portal",
            "description": "A 1-sentence description of how it helps with their missing skills.",
            "link": "The official URL"
        }}
    ]
    """

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)

        clean_text = response.text.strip()
        # Use Regex to hunt down the JSON array [ ] instead of an object { }
        match = re.search(r'\[.*\]', clean_text, re.DOTALL)
        
        if match:
            json_string = match.group(0)
            parsed_schemes = json.loads(json_string)
            print(f"✅ AI Found {len(parsed_schemes)} Relevant Schemes!")
            return parsed_schemes
        else:
            print("❌ AI returned invalid JSON for schemes.")
            return []

    except Exception as e:
        print(f"❌ Error generating schemes: {e}")
        return []