import os
import glob
from google import genai

def read_field_notes(directory):
    """Read all text files in the given directory and concatenate them."""
    notes = []
    file_pattern = os.path.join(directory, "*.txt")
    for file_path in sorted(glob.glob(file_pattern)):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            filename = os.path.basename(file_path)
            notes.append(f"--- FILE: {filename} ---\n{content}\n")
    return "\n".join(notes)

def generate_draft_report(field_notes_text: str):
    """Sends the field notes to Gemini to generate the draft report."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        api_key = input("\n[!] GEMINI_API_KEY bulunamadı.\nLütfen Gemini API anahtarınızı yapıştırın ve Enter'a basın: ").strip()
        os.environ["GEMINI_API_KEY"] = api_key

    client = genai.Client()
    
    prompt = f"""
You are an expert construction project engineer. Your task is to review the following raw field notes from multiple sources and generate a comprehensive Daily Construction Report.

Project Name: Kadikoy Bridge Rehabilitation Project (Contract #BR-2024-071)
Date of Report: March 14, 2026

INSTRUCTIONS:
1. Reconcile any conflicting details by preferring official documents (e.g., delivery tickets, safety logs) over informal notes (e.g., WhatsApp messages or voicemails).
2. Do not invent any technical data that is not present in the notes.
3. The output MUST follow the seven required elements exactly:
   1. Date, project name, report number (Assume report number DCR-048)
   2. Weather (morning + afternoon)
   3. Manpower (by trade, subcontractor, count)
   4. Equipment (status: active, idle, standby)
   5. Work performed (locations, quantities, %)
   6. Delays, issues, RFI status
   7. Safety and visitors

Ensure specific locations, quantities, and named parties are included. 
The tone must be objective and factual, suitable for a legal business record. No editorializing.

RAW FIELD NOTES:
{field_notes_text}
"""
    print("Sending notes to Gemini API (this may take a moment)...")
    
    # Using gemini-2.5-pro for high-quality text comprehension and report generation.
    response = client.models.generate_content(
        model='gemini-2.5-pro',
        contents=prompt,
    )
    return response.text

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    field_notes_dir = os.path.join(script_dir, "field_notes")
    
    print(f"Reading field notes from: {field_notes_dir}")
    notes_combined = read_field_notes(field_notes_dir)
    
    if not notes_combined.strip():
        print("No field notes found!")
        return

    try:
        draft = generate_draft_report(notes_combined)
        
        output_file = os.path.join(script_dir, "draft_report.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(draft)
            
        print(f"Successfully generated draft report! Saved to: draft_report.txt")
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Make sure you have set the GEMINI_API_KEY environment variable.")

if __name__ == "__main__":
    main()
