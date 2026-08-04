import fitz
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY # type: ignore

client = OpenAI(api_key=OPENAI_API_KEY)


def extract_text_from_pdf(uploaded_file):
    """
    Extracts text from a PDF file using PyMuPDF (fitz).
    
    Args:
        uploaded_file: The uploaded PDF file.
    
    Returns:
        str: The extracted text from the PDF file.
    """
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        page_text = page.get_text("text")
        if isinstance(page_text, str):
            text += page_text
        else:
            text += str(page_text)
    return text

def ask_openai(prompt,max_tokens=500):
    """
    Sends a prompt to the OpenAI API and returns the response.
    
    Args:
        prompt (str): The prompt to send to the OpenAI API.
        max_tokens (int): The maximum number of tokens to generate.
        
    Returns:
        str: The response from the OpenAI API.
        
    """

    Response=client.chat.completions.create( # type: ignore
        model="gpt-4o-mini",
        messages=[
        {
                "role": "user",
                "content": prompt
        }
        ],
        temperature=0.5,
        max_tokens=max_tokens
    )

    return Response.choices[0].message.content




