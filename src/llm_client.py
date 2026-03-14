import uuid
from pathlib import Path
from huggingface_hub import hf_hub_download
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
# from src.load_environment import load_env
from src.llm_service import get_llm

# GEMINI_API_KEY = load_env.GEMINI_API_KEY

REPO_ID = "Yas1n/CADomatic_vectorstore"
FILENAME_FAISS = "index.faiss"
FILENAME_PKL = "index.pkl"

faiss_path = hf_hub_download(repo_id=REPO_ID, filename=FILENAME_FAISS)
pkl_path = hf_hub_download(repo_id=REPO_ID, filename=FILENAME_PKL)
download_dir = Path(faiss_path).parent

embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = FAISS.load_local(
    str(download_dir),
    embeddings=embedding,
    allow_dangerous_deserialization=True,
    index_name="index"
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 15})

workflow = StateGraph(state_schema=MessagesState)
# llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7, api_key=GEMINI_API_KEY)
llm = get_llm()

def call_model(state: MessagesState):
    """Generate FreeCAD Python code based on conversation state and RAG context."""
    # Get the last user message
    last_user_message = state["messages"][-1].content

    # Build context dynamically using retriever
    docs = retriever.invoke(last_user_message)
    context = "\n\n".join(doc.page_content for doc in docs)

    # Build conversation history from state
    history_text = ""
    for msg in state["messages"]:
        if msg.type == "human":
            history_text += f"User: {msg.content}\n"
        elif msg.type == "ai":
            history_text += f"Assistant: {msg.content}\n"

    # Construct the prompt
    prompt = f"""
You are a helpful assistant that writes FreeCAD Python scripts from CAD instructions.
Use the following FreeCAD wiki documentation as context: {context}

Here is the conversation so far:
{history_text}

Current instruction: {last_user_message}

Respond with valid FreeCAD 1.0.1 Python code only, no extra comments.
"""

    # Call the LLM
    messages = []
    messages.append({"role": "user", "content": prompt})
    # response = llm.invoke(prompt)
    response = llm.invoke(messages=messages)
    return {"messages": [response]}

# Add nodes and edges to the graph
workflow.add_edge(START, "model")
workflow.add_node("model", call_model)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# Unique conversation ID for session persistence
thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}


def prompt_llm(user_prompt: str ,  model_name , api_key ,base_url) -> str:
    global llm = get_llm(model = model_name,
        api_key = api_key,
        base_url = base_url)
    """Send a user prompt and get the model response while preserving conversation history."""
    input_message = HumanMessage(content=user_prompt)
    response_text = ""
    for event in app.stream({"messages": [input_message]}, config, stream_mode="values"):
        response_text = event["messages"][-1].content
    return response_text

def reset_memory():
    """Start a new conversation by resetting the thread ID."""
    global thread_id, config
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
