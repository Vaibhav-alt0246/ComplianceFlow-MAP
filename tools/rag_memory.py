import os
from typing import List
from crewai.tools import tool

import chromadb
from chromadb.utils import embedding_functions


# Path to the base policies file
POLICIES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "base_policies.txt")
# ChromaDB persistence path
CHROMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "bank_policies.chroma")


def _split_policies_by_section(text: str) -> List[str]:
    """
    Split policy text into chunks by section headers.
    Sections are assumed to start with "SECTION" or lines like "1.1", "1.2", etc.
    """
    lines = text.split("\n")
    chunks = []
    current_chunk = []
    section_pattern = ["SECTION", "1.1", "1.2", "1.3", "2.1", "2.2", "3.1", "3.2", "3.3"]

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if this line starts a new section
        is_new_section = any(line.startswith(prefix) for prefix in section_pattern)

        if is_new_section and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
        else:
            current_chunk.append(line)

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks


class PolicySearchTool:
    """
    CrewAI custom tool for searching bank policies using ChromaDB RAG.
    """

    def __init__(self):
        # Initialize ChromaDB persistent client
        os.makedirs(os.path.dirname(CHROMA_PATH), exist_ok=True)
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)

        # Use basic sentence transformer embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        # Get or create the collection
        self.collection = self.client.get_or_create_collection(
            name="canara_policies",
            embedding_function=self.embedding_function
        )

        # Load and index policies if collection is empty
        if self.collection.count() == 0:
            self._index_policies()

    def _index_policies(self):
        """Read base_policies.txt and embed chunks into ChromaDB."""
        if not os.path.exists(POLICIES_FILE):
            print(f"Warning: Policies file not found at {POLICIES_FILE}")
            return

        with open(POLICIES_FILE, "r", encoding="utf-8") as f:
            policy_text = f.read()

        chunks = _split_policies_by_section(policy_text)

        if not chunks:
            print("Warning: No policy chunks found")
            return

        # Create IDs for each chunk
        ids = [f"policy_chunk_{i}" for i in range(len(chunks))]

        # Add to collection
        self.collection.add(
            documents=chunks,
            ids=ids
        )

        print(f"Indexed {len(chunks)} policy chunks into ChromaDB")

    @tool
    def search_policies(self, search_query: str) -> str:
        """
        Search the bank policy knowledge base for relevant policy chunks.

        Args:
            search_query: The search query (e.g., 'password length requirements')

        Returns:
            Top 2 most relevant policy chunks from the Chroma collection.
        """
        results = self.collection.query(
            query_texts=[search_query],
            n_results=2
        )

        if not results or not results["documents"]:
            return "No relevant policy chunks found."

        relevant_chunks = results["documents"][0]
        formatted_output = "\n\n---\n\n".join(relevant_chunks)

        return f"Relevant Policy Chunks:\n\n{formatted_output}"


# Create a singleton instance for use in CrewAI
_policy_search_tool = PolicySearchTool()
policy_search_tool = _policy_search_tool.search_policies
