import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

BASE_URL_WIKI = "https://wiki.freecad.org/Power_users_hub"
BASE_URL_GITHUB = "https://github.com/shaise/FreeCAD_FastenersWB"

DOMAIN_WHITELIST = [
    "https://wiki.freecad.org",
    "https://github.com/shaise"
]

LANG_IDENTIFIERS = [
    "/id", "/de", "/tr", "/es", "/fr", "/hr", "/it", "/pl",
    "/pt", "/pt-br", "/ro", "/fi", "/sv", "/cs", "/ru", "/zh-cn",
    "/zh-tw", "/ja", "/ko"
]

CHECKPOINT_INTERVAL = 500  # save every 500 pages

VECTORSTORE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../vectorstore")
os.makedirs(VECTORSTORE_PATH, exist_ok=True)

def is_excluded_url(url):
    url_lower = url.lower()
    if "wiki.freecad.org" in url_lower:
        if any(lang in url_lower for lang in LANG_IDENTIFIERS):
            return True
    return (
        ".jpg" in url_lower or
        ".png" in url_lower or
        "edit&section" in url_lower
    )

def crawl_wiki(start_url, max_pages):
    visited = set()
    to_visit = [start_url]
    pages = []

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited or is_excluded_url(url):
            continue
        try:
            print(f"Fetching: {url}")
            res = requests.get(url)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")
            visited.add(url)

            for tag in soup(["script", "style", "header", "footer", "nav", "aside"]):
                tag.extract()
            text = soup.get_text(separator="\n")
            clean = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
            pages.append({"url": url, "text": clean})

            # Queue internal links
            for a in soup.find_all("a", href=True):
                full = urljoin(url, a["href"])
                if any(full.startswith(domain) for domain in DOMAIN_WHITELIST):
                    if full not in visited and not is_excluded_url(full):
                        to_visit.append(full)

            # --- Checkpoint: save every N pages ---
            if len(pages) % CHECKPOINT_INTERVAL == 0:
                save_vectorstore_checkpoint(pages, checkpoint_suffix=f"checkpoint_{len(pages)}")
                print(f"Checkpoint saved after {len(pages)} pages")
        except Exception as e:
            print(f"Error fetching {url}: {e}")

    return pages

def save_vectorstore_checkpoint(pages, checkpoint_suffix="latest"):
    texts = [p["text"] for p in pages]
    metadatas = [{"source": p["url"]} for p in pages]

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    docs = splitter.create_documents(texts, metadatas=metadatas)

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(docs, embeddings)

    checkpoint_path = os.path.join(VECTORSTORE_PATH, checkpoint_suffix)
    os.makedirs(checkpoint_path, exist_ok=True)
    vectorstore.save_local(checkpoint_path)

def build_vectorstore():
    wiki_pages = crawl_wiki(BASE_URL_WIKI, max_pages=2000) #2000
    github_pages = crawl_wiki(BASE_URL_GITHUB, max_pages=450) #450
    all_pages = wiki_pages + github_pages

    if not all_pages:
        print("No pages crawled. Exiting.")
        return

    # Final save
    save_vectorstore_checkpoint(all_pages, checkpoint_suffix="final")
    print(f"Vectorstore fully saved to {VECTORSTORE_PATH}/final")

if __name__ == "__main__":
    build_vectorstore()
