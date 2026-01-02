from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os
import io
import base64
from PIL import Image
from fpdf import FPDF
import pdf2image
from google import genai
import html
import re

st.set_page_config(page_title="AI Scanner", page_icon="🤖", layout="wide")

# ---------------- GEMINI SETUP ----------------
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL_NAME = "gemini-1.5-flash"  # safer quota than 2.0

# ---------------- PDF HANDLING ----------------
@st.cache_data
def input_pdf_setup(uploaded_file_bytes):
    try:
        images = pdf2image.convert_from_bytes(uploaded_file_bytes)
        first_page = images[0]

        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format="JPEG")
        img_byte_arr = img_byte_arr.getvalue()

        pdf_parts = [{
            "mime_type": "image/jpeg",
            "data": base64.b64encode(img_byte_arr).decode()
        }]
        return pdf_parts
    except Exception as e:
        st.error(f"Error processing PDF: {e}")
        return None

# ---------------- GEMINI STREAMING ----------------
def get_gemini_response_stream(pdf_content, prompt, user_input):
    try:
        response_stream = client.models.generate_content_stream(
            model=MODEL_NAME,
            contents=[pdf_content[0], prompt, user_input]
        )

        for chunk in response_stream:
            if chunk.text:
                yield chunk.text

    except Exception:
        yield "⚠️ Gemini quota exceeded. Please retry later."

# ---------------- UI STYLES ----------------
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

if "optimized_resume_text" not in st.session_state:
    st.session_state.optimized_resume_text = ""

# ---------------- PROMPTS ----------------
input_prompt1 = """
You are an experienced Human Resources Manager with a strong technical background.
Evaluate the resume strictly against the job description.

Sections:
Strengths
Weaknesses

Keep it very detailed.
"""

input_prompt3 = """
You are an ATS system.

Return 
1. Percentage Match
2. Missing Keywords
3. Final Thoughts

Very detailed.
"""

input_prompt4 = """
Rewrite and optimize the resume perfectly for the given job description.
Fabricate realistic experience if required.

Rules:
- Output ONLY the resume text
- Start directly with candidate name
- No markdown
- No explanations
"""

# ---------------- MAIN UI ----------------
with st.container(border=True):
    uploaded_file = st.file_uploader("1. Upload Your Resume (PDF only)", type=["pdf"])
    input_text = st.text_area("2. Paste the Job Description Here", height=70)

    if uploaded_file is not None and input_text:
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            submit1 = st.button("📋 Evaluation", use_container_width=True)
        with col2:
            submit3 = st.button("📊 Match %", use_container_width=True)
        with col3:
            submit4 = st.button("📝 Optimize", use_container_width=True)
    else:
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("📋 Evaluation", disabled=True, use_container_width=True)
        with col2:
            st.button("📊 Match %", disabled=True, use_container_width=True)
        with col3:
            st.button("📝 Optimize", disabled=True, use_container_width=True)

# ---------------- RESULTS ----------------
if uploaded_file and input_text and (submit1 or submit3 or submit4):
    with st.spinner("Processing your resume..."):
        pdf_content = input_pdf_setup(uploaded_file.getvalue())

    if pdf_content:
        st.markdown("---")
        st.header("Analysis Result")
        with st.container(border=True):

            if submit1:
                st.subheader("🔎 Professional Evaluation")
                st.write_stream(
                    get_gemini_response_stream(pdf_content, input_prompt1, input_text)
                )

            elif submit3:
                st.subheader("📊 Percentage Match Analysis")
                st.write_stream(
                    get_gemini_response_stream(pdf_content, input_prompt3, input_text)
                )

            elif submit4:
                st.subheader("📝 Optimized Resume")
                optimized_text = st.write_stream(
                    get_gemini_response_stream(pdf_content, input_prompt4, input_text)
                )

                if optimized_text:
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
                    pdf.set_font("DejaVu", "", 10)

                    cleaned = html.unescape(optimized_text)
                    cleaned = re.sub(r"[*`#]", "", cleaned)
                    lines = cleaned.split("\n")
                    lines = [
                        line for line in lines
                        if "note:" not in line.lower()
                        and "here's" not in line.lower()
                    ]
                    cleaned = "\n".join(lines)

                    pdf.multi_cell(0, 5, cleaned)
                    pdf_bytes = bytes(pdf.output(dest="S"))

                    st.download_button(
                        "📥 Download Optimized Resume as PDF",
                        data=pdf_bytes,
                        file_name="optimized_resume.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
