from dotenv import load_dotenv
from langchain_groq import ChatGroq
# initiallize llm
load_dotenv()
llm=ChatGroq(model_name="llama-3.1-8b-instant",temperature=0.9)