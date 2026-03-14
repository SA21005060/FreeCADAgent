# Code for adding to the index

import os
import pickle
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

# Directories
fcmacro_dir = r"C:\Users\yasin\Desktop\Code\CADomatic files\Query2CAD\results\code"
faiss_index_dir = r"C:\Users\yasin\Desktop\Code\CADomatic files\vectorstore_for_oss120b\correct_vector"  # Existing FAISS index dir
faiss_save_dir = r"C:\Users\yasin\Desktop\Code\CADomatic files\vectorstore_for_oss120b\final_langchain\index_added_sketch"  # New save dir

# Ensure save directory exists
os.makedirs(faiss_save_dir, exist_ok=True)

# Initialize HuggingFace embeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Load .fcmacro files and tag as "sketch example"
def load_fcmacro_files(folder_path):
    docs = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".FCMacro"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                docs.append(Document(
                    page_content=content,
                    metadata={"source": file_path, "type": "sketch example"}
                ))
    return docs

# Load existing FAISS index from directory
def load_existing_index():
    index_name = "index_oss120b"  # Your FAISS index file without extension
    index_file = os.path.join(faiss_index_dir, f"{index_name}.faiss")
    if os.path.exists(index_file):
        print(f"✅ Loading existing FAISS index from {index_file}...")
        return FAISS.load_local(faiss_index_dir, embeddings, index_name=index_name, allow_dangerous_deserialization=True)
    else:
        print(f"⚠ No existing FAISS index found at {index_file}.")
        return None

# Split documents into chunks
def split_documents(docs):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )
    return text_splitter.split_documents(docs)

# Extend FAISS index with new documents
def extend_faiss_index():
    # Load existing index or create a new one
    vectorstore = load_existing_index()

    # Load new documents
    print("🔍 Loading new .fcmacro files...")
    new_docs = load_fcmacro_files(fcmacro_dir)

    if not new_docs:
        print("⚠ No new documents found.")
        return

    print(f"✅ Found {len(new_docs)} new documents.")
    chunks = split_documents(new_docs)
    print(f"✅ Split into {len(chunks)} chunks.")

    if vectorstore:
        print("➕ Adding new chunks to existing FAISS index...")
        vectorstore.add_documents(chunks)
    else:
        print("🆕 Creating new FAISS index...")
        vectorstore = FAISS.from_documents(chunks, embeddings)

    # Save updated FAISS index in the new directory
    print(f"💾 Saving updated FAISS index to {faiss_save_dir}...")
    vectorstore.save_local(faiss_save_dir)

    # Save an additional pickle as a backup
    pickle_path = os.path.join(faiss_save_dir, "vectorstore_added_sketch.pkl")
    with open(pickle_path, "wb") as f:
        pickle.dump(vectorstore, f)

    print(f"✅ Index updated successfully.")
    print(f"   ➤ FAISS files: {os.path.join(faiss_save_dir, 'index.faiss')} & index.pkl")
    print(f"   ➤ Backup pickle: {pickle_path}")

if __name__ == "__main__":
    extend_faiss_index()
