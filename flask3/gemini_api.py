import os
import json

from dotenv import load_dotenv
from google import genai
from google.genai.errors import ClientError, ServerError

# ==========================================
# Load Environment Variables
# ==========================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY environment variable is missing.")

# ==========================================
# Gemini Client
# ==========================================

client = genai.Client(
    api_key=api_key
)

# ==========================================
# Generate AI Form
# ==========================================

def generate_form(prompt):

    ai_prompt = f"""
You are an AI Google Form Generator.

Generate ONLY valid JSON.

Do NOT use markdown.
Do NOT give explanations.
Do NOT wrap JSON inside ```.

Return JSON exactly like this:

{{
    "title":"Student Feedback Form",
    "description":"Please provide your valuable feedback.",
    "questions":[
        {{
            "type":"text",
            "label":"Full Name",
            "required":true
        }},
        {{
            "type":"email",
            "label":"Email",
            "required":true
        }},
        {{
            "type":"dropdown",
            "label":"Department",
            "options":["AIML","CSE","ECE"]
        }},
        {{
            "type":"radio",
            "label":"Gender",
            "options":["Male","Female","Other"]
        }},
        {{
            "type":"checkbox",
            "label":"Skills",
            "options":[
                "Python",
                "Java",
                "Machine Learning",
                "Web Development"
            ]
        }},
        {{
            "type":"number",
            "label":"Age"
        }},
        {{
            "type":"date",
            "label":"Date"
        }},
        {{
            "type":"time",
            "label":"Preferred Time"
        }},
        {{
            "type":"rating",
            "label":"Teaching Quality"
        }},
        {{
            "type":"paragraph",
            "label":"Suggestions"
        }}
    ]
}}

Generate a form for this request:

{prompt}
"""

    try:
        
        response = client.models.generate_content(
    model="gemini-3.1-flash-lite",
    contents=ai_prompt
)
        text = response.text.strip()

        # Remove markdown if Gemini accidentally adds it
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

        return json.loads(text)

    except ServerError:

        return {
            "title": "Server Busy",
            "description": "Gemini server is busy. Please try again later.",
            "questions": []
        }

    except ClientError as e:

        error = str(e)

        if "RESOURCE_EXHAUSTED" in error:

            return {
                "title": "API Quota Exceeded",
                "description": "Gemini API quota has been exceeded. Please try again later.",
                "questions": []
            }

        elif "UNAUTHENTICATED" in error:

            return {
                "title": "Authentication Error",
                "description": "Invalid API Key.",
                "questions": []
            }

        else:

            return {
                "title": "Gemini Error",
                "description": error,
                "questions": []
            }

    except json.JSONDecodeError:

        return {
            "title": "JSON Error",
            "description": "Gemini returned an invalid JSON response.",
            "questions": []
        }

    except Exception as e:

        return {
            "title": "Unexpected Error",
            "description": str(e),
            "questions": []
        }