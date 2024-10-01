import base64
import requests # type: ignore
import json
import streamlit as st # type: ignore
from PyPDF2 import PdfReader # type: ignore
from io import BytesIO
from PIL import Image # type: ignore
from reportlab.lib.pagesizes import letter # type: ignore
from reportlab.lib import colors # type: ignore
from reportlab.lib.styles import getSampleStyleSheet # type: ignore
from reportlab.platypus import SimpleDocTemplate, Paragraph # type: ignore
from reportlab.lib.units import inch # type: ignore

# Title 
st.title("EduGen")

# Introduction
st.markdown("""

EduGen is an innovative platform designed to simplify the creation of quizzes for high school educators. It allows teachers to upload any PDF document and automatically transforms the content into a list of customizable quizzes. Here’s how it works:

**1. PDF Upload and Content Analysis**\n
Teachers begin by uploading a PDF file to EduGen. This file could be a reading passage, textbook section, or any educational material relevant to their class. Once uploaded, EduGen's advanced text-recognition system analyzes the content, identifying key points, topics, and important sections that can be turned into quiz questions.

**2. Automatic Quiz Generation**\n
After analyzing the PDF, EduGen generates a list of quizzes.
EduGen ensures that the questions are suitable for high school students and are based on the key concepts identified in the uploaded document.

**3. Editing and Customization**\n
Teachers can review the generated quizzes and edit them as needed. They can modify existing questions and  choose which questions to include in the final quiz. This allows complete flexibility in tailoring the quiz to match the lesson plan and specific student needs.

**4. Final Quiz Selection**\n
Once the teacher is satisfied with the quiz content, they can select the final list of questions that will be used for the test. EduGen makes it easy to preview the quiz before finalizing the selection.\n
In this way teachers can see the final result and decide if it suits their needs or if it needs further adjustments.

**5. Two Output Formats: For Teachers and Students**\n
EduGen generates two versions of the final quiz:

_Teacher’s Version_: This version includes the original text source from the PDF and the correct answers to all questions. It serves as an answer key, making grading faster and more efficient.

_Student’s Version_: The student version excludes the text source and correct answers, ensuring students are tested solely on their knowledge of the material without reference to the original PDF content.

Both versions are downloadable in .txt and .pdf format so that later on the file is also printable, making it convenient for teachers to distribute either digitally or in paper format.

With EduGen, creating engaging and customized quizzes is easier than ever. The platform’s automated system, combined with flexible editing features, helps teachers save time and focus on what really matters: helping students succeed.
""")
# User input: Select the quiz level
quiz_level = st.selectbox("Select the quiz level:", ["Middle school", "High school", "College"])

# File Uploader for PDFs
uploaded_files = st.file_uploader("Upload your PDF files", type="pdf", accept_multiple_files=True)

# Variable to store extracted text from PDFs
extracted_texts = []

# Initialize session state variables if not already present
if 'api_response' not in st.session_state:
    st.session_state['api_response'] = ""
if 'questions' not in st.session_state:
    st.session_state['questions'] = []

# Extract text from each uploaded PDF
if uploaded_files:
    for uploaded_file in uploaded_files:
        pdf_reader = PdfReader(uploaded_file)
        num_pages = len(pdf_reader.pages)
        
        # Extract text from each page
        extracted_text = ""
        for page in range(num_pages):
            extracted_text += pdf_reader.pages[page].extract_text()
        
        # Add the extracted text from this PDF to the list
        extracted_texts.append(extracted_text)
        # Combine extracted texts into one string
    combined_extracted_text = "".join(extracted_texts)  # Joining the list into a single string

    # Display the names of the uploaded PDFs
    st.write("You have uploaded the following PDFs:")
    for uploaded_file in uploaded_files:
        st.write(f"- {uploaded_file.name}")
    
    # Display extracted text 
    for idx, text in enumerate(extracted_texts):
        st.text_area(f"PDF {idx + 1} Text", value=text, height=200)
    #------------------------------------------------------------------- API SECTION ----------------------------------------------------------------- 
    OPENROUTER_API_KEY = "#insert here your API key"


    modello = "meta-llama/llama-3.1-8b-instruct"

    temperature = 0.5

    systemPrompt = '''You are an assistant that doesn't make mistakes.
    If a reference model is presented to you, you follow it perfectly
    without making errors.'''

    basePrompt = '''Create a high school - level quiz based on the provided text.
    You must strictly adhere to the following format without any errors:
    > [ Insert the question ]
    a ) [ Option A ]
    b ) [ Option B ]
    c ) [ Option C ]
    d ) [ Option D ]
    * Correct Answer: [Insert the letter corresponding to the correct
    answer for example : 'a)']
    * Source: [Write the exact line or passage from the provided text 
    where the information for this question can be found.] 
    **END_OF_QUESTION**

    
    Please note that you are allowed to modify only the parts within
    brackets  ([...]) in the format provided.
    Ensure that all four options are distinct.
    When mentioning a date, please make sure to specify the year.
    Immediately start by writing the questions, don't write anything else like "Here are the quizzes"
    Please remember to always write at the end of the quiz as aforementioned the word "**END_OF_QUESTION**"  '''

    finalPrompt =  finalPrompt = basePrompt.format(quiz_level=quiz_level) + "\n\n" + extracted_text

    if st.button("Deliver"):
        with st.spinner("Delivering the extracted text..."):
            response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            },
            data=json.dumps({
                "model": modello,
                "temperature": temperature,
                "messages": [
                {"role": f"{systemPrompt}" },
                { "content": f"{finalPrompt}" }
                ]
            })
            )
            # Check if the response is successful
        if response.status_code == 200:
            result = response.json()
                # Assuming the API returns the generated content in 'choices' key
                # Get the formatted response from the API
            formatted_response = result['choices'][0]['message']['content']
            
            # Save the response in the session state
            st.session_state.api_response = formatted_response
            
            # Split the response into questions based on new lines
            st.session_state['questions'] = [q.strip() for q in formatted_response.split("**END_OF_QUESTION**") if q.strip()]

    st.success("Text delivered successfully!")

# Ensure the API response and questions persist across reruns
if 'api_response' in st.session_state and st.session_state['api_response']:
    st.write("### Edit and Select Questions")
    
    # Store the selected and edited questions
    selected_questions = []

    # Iterate over the questions and display them with checkboxes and editable fields
    for i, question in enumerate(st.session_state['questions']):
        if question.strip():
            # Create a column layout with a checkbox and text area in the same row
            cols = st.columns([0.1, 0.9])  # Adjust the column ratio 
            
            # Add checkbox and editable question text side by side
            with cols[0]:
                checked = st.checkbox("", key=f"check_{i}")
            
            with cols[1]:
                edited_question = st.text_area(f"Question {i+1}", value=question.strip(), key=f"edit_{i}")

            # If the question is checked, add it to the selected list
            if checked:
                selected_questions.append(edited_question)

    # Display selected questions for confirmation
    st.write("### Selected Questions:")
    if selected_questions:
        for question in selected_questions:
            formatted_question = question.replace('\n', '  \n')  # Markdown new line (two spaces + newline) as character combo to work fine 
            st.markdown(f"{formatted_question}")

    selected_questions_text = "\n\n".join(selected_questions)

    # Download button for selected questions as a text file
    def download_text_file(text, filename):
        b64 = base64.b64encode(text.encode()).decode()  # Convert to base64
        href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">Download as Text File</a>'
        st.markdown(href, unsafe_allow_html=True)


    def download_pdf_file(text, filename):
        # Create a buffer to save the PDF in memory
        buffer = BytesIO()

        # Create a SimpleDocTemplate to build the PDF
        pdf = SimpleDocTemplate(buffer, pagesize=letter)

        # Create a list to hold elements for the PDF
        elements = []

        # Define a style for the text
        styles = getSampleStyleSheet()
        style = styles['Normal']  # You can adjust this style for customization

        # Add title or header (optional)
        header = Paragraph("<b>EDUGEN</b>", styles['Title'])
        elements.append(header)

        # Split the text into lines to avoid issues with long lines
        paragraphs = text.split('\n')

        # Add paragraphs to the elements list and wrap text inside the page's width
        for paragraph in paragraphs:
            para = Paragraph(paragraph, style)
            elements.append(para)
            elements.append(Paragraph("<br/>", style))  # Add space after each paragraph

        # Build the PDF
        pdf.build(elements)

        # Get the value of the BytesIO buffer and encode it to base64
        buffer.seek(0)
        b64 = base64.b64encode(buffer.getvalue()).decode()

        # Create a link for downloading the PDF
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">Download as PDF</a>'
        st.markdown(href, unsafe_allow_html=True)

    st.write("### Download for Teachers")
    if st.button("Teacher Questions TXT"):
        download_text_file(selected_questions_text, "Teacher Questions.txt")
    if st.button("Teacher Questions PDF"):
        download_pdf_file(selected_questions_text, "Teacher Questions.pdf")

    # Additional logic for student download
    st.write("### Download for Students")
    student_questions = []
    
    for question in selected_questions:
        # Split the question and exclude the lines after "*"
        question_lines = question.split('*')
        student_question = question_lines[0].strip()  # Get the part before '*'
        student_questions.append(student_question)

    # Convert selected questions for students to a single string
    student_questions_text = "\n\n".join(student_questions)

    # Download button for student questions as a text file
    if st.button("Student Questions TXT"):
        download_text_file(student_questions_text, "Student Questions.txt")
    if st.button("Student Question PDF"):
        download_pdf_file(student_questions_text, "Student Questions.pdf")

#----------------------------------- IMAGE SECTION OF THE CODE -----------------------------------------------
#Load the image using PIL
image = Image.open("EduOwl.png")

# Adding custom CSS for hover effect
st.markdown("""
    <style>
    .shaking-image {
        transition: transform 0.3s ease-in-out;
    }

    .shaking-image:hover {
        transform: rotate(5deg) translate(0px, -8px);
    }
    </style>
    """, unsafe_allow_html=True)

# Encode the image in base64 for use in HTML
import base64
from io import BytesIO

buffer = BytesIO()
image.save(buffer, format="PNG")
img_str = base64.b64encode(buffer.getvalue()).decode()

# Display the image using HTML with the CSS class
st.markdown(
    f"""
    <img src="data:image/png;base64,{img_str}" class="shaking-image" width="800"/>
    """,
    unsafe_allow_html=True
)

# Add custom CSS for hover effect on the text
st.markdown("""
    <style>
    .hover-text {
        transition: opacity 0.3s ease;
        color: white; /* Base color white */
        font-size: 18px;
        font-weight: bold;
        text-align: center;
    }

    .hover-text-default {
        opacity: 1;
    }

    .hover-text-hover {
        opacity: 0;
    }

    .hover-text-container:hover .hover-text-default {
        opacity: 0;
    }

    .hover-text-container:hover .hover-text-hover {
        opacity: 1;
        color: #f39c12;  /* Color when hovered */
    }

    .hover-text-container {
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Add the dynamic text with hover effect
st.markdown("""
    <div class="hover-text-container">
        <p class="hover-text hover-text-default">Thank you for using EduGen!</p>
        <p class="hover-text hover-text-hover">EduOwl wishes you the best of luck!</p>
    </div>
""", unsafe_allow_html=True)