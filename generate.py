#!/usr/bin/env python3

import os
import sys
import textwrap
from typing import List, Dict
import ollama  # Make sure to install: pip install ollama

# Sample report data (you can replace this with your text file reading logic)
MEDICAL_REPORT = """
Here's the extracted text from the image:

**Patient:** S.PAPA
**Age / Sex:** 75 Y / Female
**Referrer:** Dr. HOME COLLECTION
**Branch:** HOME COLLECTION CHN

**Report Date & Time:** 05/11/2023 17:09:04

**INVESTIGATION / METHOD** | **RESULT** | **UNITS** | **BIOLOGICAL REFERENCE INTERVAL**
---|---|---|---
**HAEMATOLOGY**
**COMPLETE BLOOD COUNT (CBC)**
RBC (Red Blood Cell Count) | 4.10 | Million/cmm | 3.8-4.8
(Method : WB/Automated)
(Specimen : EDTA WHOLE BLOOD)
Haemoglobin (HB) | 13.2 | gm/dL | 12-15
(Method : WB/Automated)
(Specimen : EDTA WHOLE BLOOD)
PCV (Haematocrit-Packed Cell Volume) | 40.0 | % | 36-46
(Method : WB/Automated)
(Specimen : EDTA WHOLE BLOOD)
MCV (Mean Corpuscular Volume) | 97.6 | fl | 83-101
(Method : WB/Automated)
(Specimen : EDTA WHOLE BLOOD)
MCH (Mean Corpuscular Haemoglobin) | 32.2 | pg | 27-32
(Method : WB/Automated)
(Specimen : EDTA WHOLE BLOOD)
MCHC (Mean Corpuscular Haemoglobin Concentration) | 33.2 | g/dL | 31-36
(Method : WB/Automated)
(Specimen : EDTA WHOLE BLOOD)
**DIFFERENTIAL WHITE BLOOD CELL COUNT (WBC DIFF)**
(Method : WB/Automated)
(Specimen : EDTA WHOLE BLOOD)
Neutrophils | 65.0 | % | 40-70
Lymphocytes | 25.0 | % | 20-40
Monocytes | 6.0 | % | 2-8
Eosinophils | 3.0 | % | 1-4
Basophils | 1.0 | % | 0-1
**PLATELET COUNT**
(Method : WB/Automated)
(Specimen : EDTA WHOLE BLOOD)
Platelet Count | 240 | x10^9/L | 150-400
MPV (Mean Platelet Volume) | 9.8 | fL | 7-11
(Method : WB/Automated)
(Specimen : EDTA WHOLE BLOOD)
P-LFC (Platelet Large Cell Fraction) | 13.9 | % | 1.9-5.1
(Method : WB/Automated)
(Specimen : EDTA WHOLE BLOOD)

**Note:**
*   WB/Automated: Whole Blood/Automated Analyzer
*   fL: Femtoliter
*   x10^9/L: Million per Liter
*   pg: Picogram
*   g/dL: Gram per Deciliter
*   cmm: Cubic Millimeter

Here's the extracted text from the image:

**Patient:** S.PAPA
**Age / Sex:** 75 Y / Female
**Referrer:** Dr. HOME COLLECTION
**Branch:** HOME COLLECTION CHN

**SID No.:** 104057905
**Reg Date & Time:** 05/11/2023 09:30:22
**Coll Date & Time:** 05/11/2023 11:36:15
**Report Date & Time:** 05/11/2023 17:09:04

**INVESTIGATION / METHOD** | **RESULT** | **UNITS** | **BIOLOGICAL REFERENCE INTERVAL**
---|---|---|---
Erythrocyte Sedimentation Rate (ESR) (Wintringham Method) |  |  |
1 Hour (Specimen: EDTA WHOLE BLOOD) | 9 | mm/hr | <35

**Additional Notes:**

*   The image also includes logos for Aarthi Scans & Labs, Siemens, and NABL accreditation.
*   There are contact details and addresses for various locations (Mumbai, Delhi, Bangalore, etc.) at the bottom of the image.

Here's the extracted text from the image:

**Patient:** S.PAPA
**Age / Sex:** 75 Y / Female
**Referrer:** Dr. HOME COLLECTION
**Branch:** HOME COLLECTION CHN

**Report Details:**
*   **SID No.:** 104057905
*   **Reg Date & Time:** 05/11/2023 09:30:22
*   **Coll Date & Time:** 05/11/2023 11:36:42
*   **Report Date & Time:** 05/11/2023 17:09:04

**Investigation / Method** | **Result** | **Units** | **Biological Reference Interval**
---|---|---|---
**BIOCHEMISTRY**
GLUCOSE (RBS) | 242.0 | mg/dL | 80-140
(Method: Glucose Oxidase - Peroxidase)
(Specimen: FLUORIDE EDTA PLASMA)
BIOCHEMISTRY
CREATININE | 0.5 | mg/dL | 0.5 - 1.2
(Method: Jaffe, Alkaline picrate)
(Specimen: SERUM)
Aspartate aminotransferase (AST/SGOT) | 17.0 | U/L | <31
(Method: Modified IFCC)
(Specimen: SERUM)
Alanine aminotransferase (ALT/SGPT) | 31.0 | U/L | <34
(Method: IFCC)
(Specimen: SERUM)
**SEROLOGY**
CRP (C-reactive protein) | 3.70 | mg/L | Upto 5
(Method: Nephelometry)
(Specimen: SERUM)

**End of the Report**

**Dr.C.GUPTHASAD MD.,**
**Pathologist**

---

**Additional Information from the Image:**

*   **Location Information:** Mumbai, Delhi, Bangalore, Chennai, Hyderabad, Kolkata, Vizag, Guwahati, Trivandrum, Pune, Pondicherry
*   **Disclaimer:** "The color of urine should not be taken as a diagnostic parameter, but rather as an indicator of hydration."
"""

def initialize_chatbot() -> None:
    """Check if Ollama is running and pull the model if needed."""
    try:
        ollama.list()
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        print("Please make sure Ollama is running (run 'ollama serve' in terminal)")
        sys.exit(1)
    
    # Use mistral model (you can change to gemma or others)
    model = "mistral"
    try:
        ollama.show(model)
    except ollama.ResponseError:
        print(f"Downloading {model} model (this may take a while)...")
        ollama.pull(model)

def explain_report(report_text: str) -> str:
    """Get a simplified explanation of the medical report."""
    prompt = f"""
    Here is a medical lab report:

    {report_text}

    Please explain this report in simple, non-medical terms that a normal person can understand.
    Focus on:
    1. The patient's overall health based on the results
    2. Any values that are outside normal ranges and what that might mean
    3. General advice based on the results
    4. Whether they should consult a doctor about any specific results

    Organize your response in clear sections with headings.
    Use bullet points for easy reading.
    Be reassuring but honest about any concerns.
    """
    
    response = ollama.generate(
        model='gemma3:12b',
        prompt=prompt,
        options={'temperature': 0.3}  # Lower temperature for more factual responses
    )
    return response['response']

def answer_question(report_text: str, question: str) -> str:
    """Answer a specific question about the medical report."""
    prompt = f"""
    Here is a medical lab report:

    {report_text}

    The user asks: {question}

    Please answer this question in simple, non-medical terms that a normal person can understand.
    If the question requires medical expertise beyond explaining the report, say "You should consult your doctor about this."
    Be accurate but use simple language.
    """
    
    response = ollama.generate(
        model='gemma3:12b',
        prompt=prompt,
        options={'temperature': 0.3}
    )
    return response['response']

def main():
    initialize_chatbot()
    
    print("\n" + "="*50)
    print("MEDICAL REPORT EXPLAINER".center(50))
    print("="*50 + "\n")
    
    # Get the simplified explanation
    print("Generating easy-to-understand summary of your report...\n")
    explanation = explain_report(MEDICAL_REPORT)
    print(textwrap.fill(explanation, width=80) + "\n")
    
    # Interactive Q&A
    print("\nYou can now ask questions about your report (type 'quit' to exit)")
    while True:
        question = input("\nWhat would you like to know about your report? ").strip()
        if question.lower() in ('quit', 'exit', 'q'):
            break
            
        if not question:
            continue
            
        print("\nThinking...\n")
        answer = answer_question(MEDICAL_REPORT, question)
        print(textwrap.fill(answer, width=80))

if __name__ == "__main__":
    main()