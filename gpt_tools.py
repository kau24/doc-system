import os
from openai import OpenAI

# Initialize the OpenAI client using your API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_gpt4_summary(referral_data):
    """
    Generate a clinical summary and suggestions from GPT-4 based on referral data.

    Parameters:
    - referral_data (dict): A dictionary containing referral fields like
      patient_name, age, gender, clinical_information, diagnosis, reason_for_referral, medical_history, medications

    Returns:
    - str: The GPT-4-generated summary and suggestions text
    """
    prompt = f"""
You are a clinical decision-support assistant. A referring doctor has submitted a medical referral with the following data:

Patient Name: {referral_data.get('patient_name', 'N/A')}
Age: {referral_data.get('patient_age', 'N/A')}
Gender: {referral_data.get('patient_gender', 'N/A')}

Clinical Summary:
{referral_data.get('clinical_information', 'N/A')}

Working Diagnosis:
{referral_data.get('diagnosis', 'N/A')}

Reason for Referral:
{referral_data.get('reason_for_referral', 'N/A')}

Medical History:
{referral_data.get('medical_history', 'None')}

Current Medications:
{referral_data.get('medications', 'None')}

Instructions:
1. Provide a clear summary of the case.
2. Suggest possible areas the consulting doctor may want to focus on.
3. Recommend any preliminary actions or questions to consider.

Respond in a concise and professional format.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[GPT Error] Failed to generate summary: {e}")
        return "AI summary unavailable due to a processing error."

