import os
import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from typing import List, Optional, Tuple


class PDFRAGPipeline:
    """
    RAG Pipeline for integrating protein structure analysis with literature
    """

    def __init__(self, openai_api_key: str):
        """Initialize the RAG pipeline with OpenAI API key"""
        self.openai_api_key = openai_api_key
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.1,
            openai_api_key=openai_api_key
        )
        self.vector_store_path = "faiss_db"

    def extract_text_from_pdfs(self, pdf_files: List) -> str:
        """
        Extract text from uploaded PDF files

        Args:
            pdf_files: List of uploaded PDF files from Streamlit

        Returns:
            str: Combined text from all PDFs
        """
        text = ""
        try:
            for pdf_file in pdf_files:
                pdf_reader = PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            st.error(f"Error extracting text from PDFs: {e}")
            return ""

        return text

    def create_text_chunks(self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
        """
        Split text into chunks for vector storage

        Args:
            text: Input text to split
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks

        Returns:
            List[str]: List of text chunks
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        chunks = text_splitter.split_text(text)
        return chunks

    def create_vector_store(self, text_chunks: List[str]) -> bool:
        """
        Create and save FAISS vector store from text chunks

        Args:
            text_chunks: List of text chunks

        Returns:
            bool: Success status
        """
        try:
            if not text_chunks:
                return False

            vector_store = FAISS.from_texts(text_chunks, embedding=self.embeddings)
            vector_store.save_local(self.vector_store_path)
            return True
        except Exception as e:
            st.error(f"Error creating vector store: {e}")
            return False

    def load_vector_store(self) -> Optional[FAISS]:
        """
        Load existing FAISS vector store

        Returns:
            FAISS vector store or None if not found
        """
        try:
            vector_store = FAISS.load_local(
                self.vector_store_path,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            return vector_store
        except Exception as e:
            return None

    def search_literature(self, query: str, k: int = 5) -> str:
        """
        Search literature using vector similarity

        Args:
            query: Search query
            k: Number of documents to retrieve

        Returns:
            str: Combined relevant text from literature
        """
        vector_store = self.load_vector_store()
        if not vector_store:
            return "No literature database available."

        try:
            retriever = vector_store.as_retriever(search_kwargs={"k": k})
            docs = retriever.get_relevant_documents(query)

            # Combine documents with source info
            context_parts = []
            for i, doc in enumerate(docs):
                context_parts.append(f"[Excerpt {i + 1}]: {doc.page_content}")

            return "\n\n".join(context_parts)[:4000]  # Limit context length

        except Exception as e:
            return f"Literature search failed: {e}"

    def generate_analysis_with_gpt(self,
                                   structure_data: str,
                                   literature_context: str = "",
                                   has_literature: bool = False) -> str:
        """
        Generate analysis using GPT with optional literature context

        Args:
            structure_data: Structural analysis data
            literature_context: Relevant literature context
            has_literature: Whether literature context is available

        Returns:
            str: Generated analysis
        """

        if has_literature and literature_context:
            system_prompt = """You are a structural biology expert analyzing protein-ligand complexes. 
            You have access to both structural prediction data and relevant scientific literature.
            Provide comprehensive, scientific analysis that integrates both sources."""

            user_prompt = f"""
                            STRUCTURAL ANALYSIS DATA:
                            {structure_data}

                            RELEVANT LITERATURE CONTEXT:
                            {literature_context}

                            Please provide a comprehensive analysis that:
                                1. Explains the structural findings and confidence scores
                                2. Relates findings to similar cases from the literature
                                3. Discusses prediction reliability and experimental validation
                                4. Suggests implications for drug design or protein function
                                5. Identifies any discrepancies between predictions and literature

                            Keep the response scientific and focused, suitable for researchers.
                            """
        else:
            system_prompt = """You are a structural biology expert analyzing protein-ligand complexes.
            Provide scientific analysis based on structural prediction data."""

            user_prompt = f"""
                        STRUCTURAL ANALYSIS DATA:
                        {structure_data}

                        Please provide an analysis that:
                            1. Explains the structural findings and confidence scores  
                            2. Interprets what confidence levels mean for prediction reliability
                            3. Suggests implications for drug design or protein function
                            4. Recommends experimental validation approaches
                            5. Discusses limitations of computational predictions

                            Keep the response scientific and focused, suitable for researchers.
                        """

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            response = self.llm.invoke(messages)
            return response.content

        except Exception as e:
            return f"Analysis generation failed: {e}"

    def answer_question(self, question: str, structure_context: str = "") -> str:
        """
        Answer user questions using RAG + GPT

        Args:
            question: User's question
            structure_context: Current structural analysis context

        Returns:
            str: Answer to the question
        """
        # Enhanced query with structure context
        enhanced_query = f"""
        Structural Context: {structure_context}
        Question: {question}

        Please provide information about protein structure analysis, binding predictions, 
        confidence scores, or experimental validation related to this query.
        """

        # Search literature
        literature_context = self.search_literature(enhanced_query)

        # Generate answer
        system_prompt = """You are a structural biology expert. Answer questions about 
        protein structures, binding predictions, and experimental validation using both 
        the current structural analysis context and relevant literature."""

        user_prompt = f"""
                    CURRENT STRUCTURAL CONTEXT:
                    {structure_context}

                    RELEVANT LITERATURE:
                    {literature_context}

                    USER QUESTION: {question}

                    Please provide a comprehensive answer that addresses the question using both 
                    the structural context and literature information. If the literature doesn't 
                    contain relevant information, focus on the structural analysis.
                    """

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            response = self.llm.invoke(messages)
            return response.content

        except Exception as e:
            return f"Unable to generate answer: {e}"

    def process_literature(self, pdf_files: List) -> Tuple[bool, str]:
        """
        Complete pipeline to process uploaded literature

        Args:
            pdf_files: List of uploaded PDF files

        Returns:
            Tuple[bool, str]: Success status and message
        """
        if not pdf_files:
            return False, "No PDF files provided"

        # Check file sizes
        total_size = sum([len(pdf.getvalue()) for pdf in pdf_files])
        if total_size > 50 * 1024 * 1024:  # 50MB limit
            return False, "Total PDF size exceeds 50MB limit"

        # Extract text
        text = self.extract_text_from_pdfs(pdf_files)
        if not text.strip():
            return False, "No text extracted from PDFs"

        # Create chunks
        chunks = self.create_text_chunks(text)
        if not chunks:
            return False, "Failed to create text chunks"

        # Create vector store
        success = self.create_vector_store(chunks)
        if success:
            return True, f"Successfully processed {len(pdf_files)} PDF(s) into {len(chunks)} chunks"
        else:
            return False, "Failed to create vector store"

    def is_literature_available(self) -> bool:
        """Check if literature database is available"""
        return self.load_vector_store() is not None


def initialize_rag_pipeline() -> Optional[PDFRAGPipeline]:
    """
    Initialize RAG pipeline with API key from Streamlit secrets

    Returns:
        ProteinRAGPipeline instance or None if API key not available
    """
    try:
        # Try to get API key from secrets first
        if 'OPENAI_API_KEY' in st.secrets:
            api_key = st.secrets['OPENAI_API_KEY']
        else:
            # Fallback to user input
            api_key = st.sidebar.text_input(
                'Enter OpenAI API key:',
                type='password',
                help="Get your API key from https://platform.openai.com"
            )

            if not api_key:
                return None

            if not api_key.startswith('sk-'):
                st.sidebar.warning('⚠️ OpenAI API key should start with "sk-"')
                return None

        return PDFRAGPipeline(api_key)

    except Exception as e:
        st.error(f"Failed to initialize RAG pipeline: {e}")
        return None