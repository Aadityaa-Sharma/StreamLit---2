 🧠 ATS Resume Analyzer using Google Gemini + Streamlit

This is an AI-powered Resume Analyzer and Optimizer built with **Google Gemini 1.5 Flash** and **Streamlit**. It helps job seekers tailor their resumes to job descriptions by simulating how an Applicant Tracking System (ATS) would evaluate resumes.

✨ Features

✅ Upload your resume (PDF format)  
✅ Paste a job description  
✅ Get a professional evaluation of your resume  
✅ See match percentage + missing keywords  
✅ Generate an optimized, ATS-friendly resume  
✅ Download the new resume as a PDF

 🛠 Tech Stack

- Python 3.9+
- Streamlit
- Google Generative AI SDK (`google-generativeai`)
- `pdf2image`, `Pillow`, `fpdf`, `base64`
- `python-dotenv` for environment variable handling


🚀 How to Run Locally

 1. Clone the Repository
    git clone https://github.com/beryl32/ats-resume-analyzer.git
   
    cd ats-resume-analyzer

2. Install Dependencies
   
    pip install -r requirements.txt

3. Add Your Gemini API Key

   Create a .env file in the root directory and paste your API key:

   GOOGLE_API_KEY=your_gemini_api_key_here

4. Run the Streamlit App

   streamlit run app.py


🧠 How It Works

1. The user uploads a PDF resume.

2. The app converts the first page to an image using pdf2image.

3. The image is encoded to Base64 and sent along with a job description to Google Gemini.

4. Gemini analyzes the resume:

5. Evaluates it

6. Matches it against job description

7. Suggests improvements

8. The user can download a professionally rewritten resume as a PDF.



🔒 Important Notes

 1. Only the first page of the PDF is currently analyzed.

 2. The app requires Poppler for PDF-to-image conversion (on Windows).


