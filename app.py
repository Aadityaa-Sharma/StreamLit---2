from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os
import io
import base64
from PIL import Image
from fpdf import FPDF
import pdf2image
import google.generativeai as genai
import html
import re


st.set_page_config(page_title="AI Scanner", page_icon="🤖", layout="wide")



# Configure Gemini API from the .env file
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

@st.cache_data
def input_pdf_setup(uploaded_file_bytes):
    """
    Converts the uploaded PDF file (as bytes) into an image format that Gemini can process.
    Works seamlessly on Streamlit Community Cloud without specifying poppler_path.
    """
    try:
        # Streamlit Cloud already includes Poppler in the environment
        images = pdf2image.convert_from_bytes(uploaded_file_bytes)
        first_page = images[0]

        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        pdf_parts = [{
            "mime_type": "image/jpeg",
            "data": base64.b64encode(img_byte_arr).decode()
        }]
        return pdf_parts
    except Exception as e:
        st.error(f"Error processing PDF: {e}. Ensure Poppler is available in the environment.")
        return None

def get_gemini_response_stream(pdf_content, prompt, user_input):
    """
    Calls the Gemini API with streaming enabled.
    """
    model = genai.GenerativeModel("gemini-2.0-flash")
    response_stream = model.generate_content([pdf_content[0], prompt, user_input], stream=True)
    for chunk in response_stream:
        if hasattr(chunk, 'text'):
            yield chunk.text

# --- REDESIGNED STREAMLIT UI ---

# Use CSS to remove extra padding at the top and clean up the UI
st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .stButton>button {
            font-weight: 600;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🧠 AI-Powered ATS Resume Analyzer")
st.write("Get an instant, AI-driven analysis of your resume against any job description.")

# Store analysis result in session state
if 'optimized_resume_text' not in st.session_state:
    st.session_state.optimized_resume_text = ""

# Prompts

input_prompt1 = """
You are an experienced Human Resources Manager with a strong technical background in roles such as Data Science, Full Stack Development, Web Development, Big Data Engineering, DevOps, or Data Analysis.
Your task is strictly to review the candidate’s resume against the provided job description and generate a professional, structured evaluation.
Follow these exact instructions:
1.Do not add any introductory or closing statements.
2.Do not include any self-references, assumptions, or explanations.
3.The output must only contain the evaluation, written in a formal HR tone.
4.The evaluation must be divided into two clear sections:
5.Strengths: List and describe all aspects of the resume that align well with the job description.
6.Weaknesses: List and describe areas where the candidate’s profile does not meet or only partially meets the job requirements.
Focus on skills, experience, projects, certifications, tools, and achievements that are directly relevant to the role.
Maintain professional, concise yet detailed, and objective language throughout.
Your output should only be the evaluation, formatted exactly as described above.
"""

input_prompt3 = """
You are a highly accurate ATS (Applicant Tracking System) with in-depth knowledge of technical roles such as Data Science, Full Stack Development, Web Development, Big Data Engineering, DevOps, and Data Analysis.
Your task is to analyze the candidate’s resume against the provided job description and generate an objective, structured evaluation.
Follow these exact instructions:
Do not include any explanations, reasoning steps, or additional commentary.
Do not add introductory or closing statements.
The response must only include the three sections listed below, in this exact format:
1. Percentage Match:
Provide an exact percentage (0–100%) indicating how well the resume matches the job description based on relevant skills, tools, experience, and qualifications.
2. Missing Keywords:
List all critical technical and non-technical keywords, skills, or tools from the job description that are not present or insufficiently represented in the resume.
3. Final Thoughts:
Summarize the overall suitability of the candidate for the role in a brief, professional statement (2–4 sentences), highlighting alignment level and potential gaps.
Your output must contain only these three sections in the specified order and format.
"""

input_prompt4 = """
You are an expert technical resume writer and career strategist, specializing in ATS-friendly, job-optimized resumes.  
Your task is to transform the provided resume into a perfect fit for the given job description by rewriting, fabricating where necessary, and optimizing every section to make it look highly aligned to the role.

**Follow these steps with extreme precision:**

Step 1: Pre-Analysis (Internal Reasoning — DO NOT show this in the output)
1. Analyze the provided job description (JD) and extract the top 5–10 most critical keywords, skills, and responsibilities required for the position. For example: "Solidity," "Ethereum," "Smart Contracts," "DeFi," "Blockchain Architecture."
2. Review the candidate's existing resume and map current experiences, skills, and projects to identify gaps and opportunities for improvement.

Step 2: Rewrite the Resume (This is the ONLY content you will output)
- Rewrite the resume completely to integrate the keywords and skills identified from the JD naturally and professionally.
- Adapt the content to make the candidate look like a strong fit for the role, even if it requires **adding or fabricating relevant experience, projects, or technical expertise**. Ensure fabrications are realistic, industry-appropriate, and aligned with current technology trends.
- Rewrite Experience and Projects:
  - Convert existing bullet points to match the targeted job requirements.
  - Include measurable results, achievements, and action verbs.
  - Ensure every point reflects value and impact aligned to the JD.
- Tailor the Summary:
  - Create a concise, powerful 2–3 line professional summary that highlights the candidate’s expertise and alignment to the role.
  - Integrate keywords naturally without keyword stuffing.
- Organize Skills:
  - Create a clearly structured Skills section.
  - Place the most relevant and high-priority technologies at the top.
  - Create relevant subsections (e.g., "Blockchain Technologies," "Programming & Tools," etc.) when appropriate.
- Ensure ATS Optimization:
  - Use clean, professional formatting.
  - No graphics, tables, or uncommon symbols.
  - Keep the resume concise enough to fit on one page while maximizing keyword relevance.

**Critical Output Rules:**
- The final output MUST be only the plain text of the rewritten resume.
- Begin the output directly with the candidate’s name.
- Do NOT include explanations, reasoning, or notes in the output.
- Do NOT start with phrases like “Here’s your resume” or add markdown.
- Keep the tone professional, realistic, and results-driven.

Inputs for you:
- Current Resume: [Paste the candidate’s resume here]
- Job Description: [Paste the complete job description here]

Your output should be a fully optimized, tailored, single-page resume that would stand out for this job posting.
"""
       
# --- Main UI Container ---
with st.container(border=True):
    uploaded_file = st.file_uploader("1. Upload Your Resume (PDF only)", type=["pdf"])
    
    # **FIX:** Reduced the height of the text area
    input_text = st.text_area("2. Paste the Job Description Here", height=70)

    # **FIX:** Buttons are now inside the main container and appear only when ready
    if uploaded_file is not None and input_text:
        st.divider()
        st.write("3. Choose an Analysis:")
        
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            submit1 = st.button("📋 Evaluation", use_container_width=True)
        with col_btn2:
            submit3 = st.button("📊 Match %", use_container_width=True)
        with col_btn3:
            submit4 = st.button("📝 Optimize", use_container_width=True)
    else:
        # Keep placeholder buttons to prevent layout shifts
        st.divider()
        st.write("3. Choose an Analysis:")
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            st.button("📋 Evaluation", use_container_width=True, disabled=True)
        with col_btn2:
            st.button("📊 Match %", use_container_width=True, disabled=True)
        with col_btn3:
            st.button("📝 Optimize", use_container_width=True, disabled=True)

# --- Results Section ---
if 'submit1' in st.session_state and st.session_state.submit1:
    # This logic block structure ensures that when a button is clicked,
    # it stays active through the rerun, allowing the code inside to execute.
    # This check is conceptual for Streamlit's button behavior.
    # In practice, we check the button state directly after it's defined.
    pass # Placeholder for conceptual clarity

if (uploaded_file is not None and input_text) and (submit1 or submit3 or submit4):
    with st.spinner("Processing your resume..."):
        pdf_content = input_pdf_setup(uploaded_file.getvalue())

    if pdf_content:
        st.markdown("---")
        st.header("Analysis Result")
        response_container = st.container(border=True)
        
        with response_container:
            if submit1:
                st.subheader("🔎 Professional Evaluation")
                st.write_stream(get_gemini_response_stream(pdf_content, input_prompt1, input_text))
            
            elif submit3:
                st.subheader("📊 Percentage Match Analysis")
                st.write_stream(get_gemini_response_stream(pdf_content, input_prompt3, input_text))

            elif submit4:
                st.subheader("📝 Optimized Resume")
                st.session_state.optimized_resume_text = st.write_stream(get_gemini_response_stream(pdf_content, input_prompt4, input_text))
                
                if st.session_state.optimized_resume_text:
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
                    pdf.set_font('DejaVu', '', 10)
                    
                    cleaned_text = html.unescape(st.session_state.optimized_resume_text)
                    cleaned_text = re.sub(r'[\*`#]', '', cleaned_text)
                    lines = cleaned_text.split('\n')
                    lines = [line for line in lines if "note:" not in line.lower() and "here's a revised" not in line.lower()]
                    cleaned_text = '\n'.join(lines)
                    
                    pdf.multi_cell(0, 5, cleaned_text)
                    
                    pdf_bytes = bytes(pdf.output(dest='S'))

                    st.download_button(
                        label="📥 Download Optimized Resume as PDF",
                        data=pdf_bytes,
                        file_name="optimized_resume.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
