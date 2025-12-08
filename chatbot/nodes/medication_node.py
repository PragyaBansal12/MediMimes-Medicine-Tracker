from chatbot.state import State
from chatbot.llm import llm


# --------------------------rag node-----------------------------
# 1. Load Structured CSV and Build Mini-Docs
import csv
from langchain.schema import Document

def load_medication_docs(csv_path):
    docs = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            drug = row["drug"]

            def add_doc(field_name, field_value):
                if field_value and field_value.strip():
                    docs.append(Document(
                        page_content=f"{drug} — {field_name}: {field_value}",
                        metadata={"drug": drug, "field": field_name}
                    ))

            add_doc("Brands in India", row["brands_india"])
            add_doc("Indications", row["indications"])
            add_doc("Administration", row["administration"])
            add_doc("Notes", row["notes"])

    return docs

# embedding model
from langchain_google_genai import GoogleGenerativeAIEmbeddings
embedding_model = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

# vector store creation
import os
from langchain_community.vectorstores import Chroma

DB_PATH = "./med_db"

def create_vector_db(docs):
    return Chroma.from_documents(
        documents=docs,
        embedding=embedding_model,
        persist_directory=DB_PATH
    )

def load_vector_db():
    if os.path.exists(DB_PATH):
        return Chroma(
            persist_directory=DB_PATH,
            embedding_function=embedding_model
        )
    return None


# build vector db 
import os

# Determine project root dynamically
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

CSV_PATH = os.path.join(BASE_DIR, "chatbot", "resources", "medicines_csv.csv")

docs = load_medication_docs(CSV_PATH)

vector_store = load_vector_db()

if vector_store is None:
    print("Building fresh medication DB...")
    vector_store = create_vector_db(docs)
else:
    print("Loaded existing DB.")

# retriever
retriever = vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 4, "lambda_mult": 0.7},
)


# medical_rag_node : just retrieves context from vector db
def medication_rag_node(State: State) -> State:
    query = State.get("user_input", "")
    MAX_TOKENS = 250

    def trim(x):
        return x[:MAX_TOKENS]

    try:
        docs = retriever.invoke(query)
    except Exception as e:
        State["medical_rag_context"] = {
            "error": str(e),
            "results": [],
            "metadata": [],
            "empty": True
        }
        return State

    # If nothing found
    if not docs:
        State["medical_rag_context"] = {
            "results": [],
            "metadata": [],
            "empty": True
        }
        return State

    # Group by drug
    grouped = {}
    for d in docs:
        drug = d.metadata["drug"]
        grouped.setdefault(drug, []).append(trim(d.page_content))

    State["medication_context"] = {
        "type": "medication_context",
        "results": [trim(d.page_content) for d in docs],
        "metadata": [d.metadata for d in docs],
        "grouped_by_drug": grouped,
        "empty": False
    }

    return State


