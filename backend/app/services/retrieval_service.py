import asyncio
import os
from typing import List, Dict, Any
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv

load_dotenv()


class ConversationalRAGSystem:
    def __init__(self, chroma_db_path: str = "./chroma_db", google_api_key: str = None):
        """
        Initialize the conversational RAG system with existing Chroma vector store.

        Args:
            chroma_db_path: Path to existing Chroma database
            google_api_key: Google API key for Gemini (can also be set via environment variable)
        """

        # Initialize embeddings with all-MiniLM-L6-v2
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        # Load existing Chroma vector store
        self.vector_store = Chroma(
            persist_directory=chroma_db_path,
            embedding_function=self.embeddings,
            collection_name="indian_law_acts"  # Ensure this matches your collection name
        )

        # Initialize Gemini LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.4,
            convert_system_message_to_human=True
        )

        # Initcialize conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            input_key="input",
            output_key="answer"
        )

        # Chat history for session management
        self.chat_history = []

        # Setup retrieval chain
        self._setup_retrieval_chain()

    def _setup_retrieval_chain(self):
        """Set up the conversational retrieval chain using latest LangChain patterns."""

        # Create retriever from vector store
        retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 10}
        )

        # Contextualize question prompt for history-aware retrieval
        contextualize_q_system_prompt = """Given a chat history and the latest user question \
        which might reference context in the chat history, formulate a standalone question \
        which can be understood without the chat history. Do NOT answer the question, \
        just reformulate it if needed and otherwise return it as is."""

        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])

        # Create history-aware retriever
        self.history_aware_retriever = create_history_aware_retriever(
            self.llm, retriever, contextualize_q_prompt
        )

        # QA system prompt
        qa_system_prompt = """You are an assistant for question-answering tasks. \
        Use the following pieces of retrieved context to answer the question. \
        If you don't know the answer, just say that you don't know. \
        keep the answer concise. If the question is very general like Hi or Hello then normally reply with a greeting.
        
        Context: {context}"""

        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])

        # Create question-answer chain
        question_answer_chain = create_stuff_documents_chain(
            self.llm, qa_prompt)

        # Create final RAG chain
        self.rag_chain = create_retrieval_chain(
            self.history_aware_retriever, question_answer_chain
        )

    def ask(self, question: str) -> Dict[str, Any]:
        """
        Ask a question with conversation history awareness.

        Args:
            question: User's question

        Returns:
            Dictionary containing answer, context, and metadata
        """
        try:
            # Invoke the RAG chain with chat history
            response = self.rag_chain.invoke({
                "input": question,
                "chat_history": self.chat_history
            })

            # Update chat history
            self.chat_history.extend([
                HumanMessage(content=question),
                AIMessage(content=response["answer"])
            ])

            # Store in memory for compatibility
            self.memory.save_context(
                {"input": question},
                {"answer": response["answer"]}
            )

            return {
                "question": question,
                "answer": response["answer"],
                "source_documents": response.get("context", []),
                "chat_history_length": len(self.chat_history)
            }

        except Exception as e:
            return {
                "question": question,
                "answer": f"Error processing question: {str(e)}",
                "source_documents": [],
                "chat_history_length": len(self.chat_history)
            }

    def clear_history(self):
        """Clear conversation history."""
        self.chat_history = []
        self.memory.clear()
        print("Conversation history cleared.")

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get formatted conversation history."""
        history = []
        for i in range(0, len(self.chat_history), 2):
            if i + 1 < len(self.chat_history):
                history.append({
                    "human": self.chat_history[i].content,
                    "ai": self.chat_history[i + 1].content
                })
        return history


def main():
    """Main function to demonstrate the conversational RAG system."""

    # Initialize the system (make sure to set your Google API key)
    # You can set it as an environment variable: export GOOGLE_API_KEY="your-api-key"
    rag_system = ConversationalRAGSystem(
        chroma_db_path="./chroma_db",
        # Uncomment and add your key if not using env var
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    print("🤖 Conversational RAG System Initialized!")
    print("📚 Using existing Chroma vector store from './chroma_db'")
    print("🔤 Embeddings: all-MiniLM-L6-v2")
    print("🧠 LLM: Google Gemini Pro")
    print("💬 Conversation history is maintained across questions")
    print("\nType 'quit' to exit, 'clear' to clear history, 'history' to view conversation\n")

    while True:
        try:
            # Get user input
            user_input = input("❓ Ask a question: ").strip()

            if user_input.lower() == 'quit':
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'clear':
                rag_system.clear_history()
                continue
            elif user_input.lower() == 'history':
                history = rag_system.get_conversation_history()
                if history:
                    print("\n📜 Conversation History:")
                    for i, exchange in enumerate(history, 1):
                        print(f"\n{i}. Human: {exchange['human']}")
                        print(f"   AI: {exchange['ai']}")
                else:
                    print("📭 No conversation history yet.")
                continue
            elif not user_input:
                print("⚠️  Please enter a question.")
                continue

            # Get response
            print("\n🔍 Processing your question...")
            response = rag_system.ask(user_input)

            # Display response
            print(f"\n💡 Answer: {response['answer']}")
            print(
                f"📊 Retrieved {len(response['source_documents'])} relevant documents")
            print(
                f"💬 Chat history length: {response['chat_history_length']} messages")

            # Show source documents if available
            if response['source_documents']:
                print("\n📚 Source Documents:")
                # Show first 2
                for i, doc in enumerate(response['source_documents'], 1):
                    preview = doc.page_content
                    print(f"  {i}. {preview}")

            print("\n" + "="*50)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Please try again or type 'quit' to exit.")


if __name__ == "__main__":
    main()
