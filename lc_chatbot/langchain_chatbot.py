# Import necessary libraries and modules
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define the Chatbot class
class Chatbot: 
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-pro", api_key=os.getenv("GOOGLE_API_KEY"))
        self.tools = []
        self.prompt = None
        self.agent_executor = None
        self.memory = ConversationBufferWindowMemory(
            k=5, memory_key="chat_history", return_messages=True
        )
        self.retriever = None
        # Set up the agent after initialization
        self.setup_agent()

    @tool
    def rag_tool(self, query: str) -> str:
        """
        A tool to perform RAG (Retrieval Augmented Generation).
        Use this tool to answer questions from uploaded documents.
        """
        # Check if a retriever is set
        if not self.retriever:
            return "No retriever is set."
        # Invoke the retriever with the query
        docs = self.retriever.invoke(query)
        # Check if relevant documents are found
        if not docs:
            return "No relevant documents found."
        # Return the content of the found documents
        return "\n\n".join([doc.page_content for doc in docs])

    def setup_agent(self):
        # Define the agent prompt with system message, chat history, human input, and agent scratchpad
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a helpful assistant."),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
                MessagesPlaceholder(variable_name="tools"),
                MessagesPlaceholder(variable_name="tool_names"),
            ]
        )

        # Create the agent using the language model, tools, and prompt
        self.agent = create_react_agent(self.llm, self.tools, self.prompt)

        # Create the agent executor to run the agent
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            prompt=self.prompt,
            verbose=True,
            memory=self.memory,
            handle_parsing_errors=False,  # Robust error handling (temporarily disabled for debugging)
        )

    def set_retriever(self, retriever):
        # Set the retriever for RAG
        self.retriever = retriever
        # Register tools: RAG (Retrieval Augmented Generation) and Tavily search
        self.tools = [self.rag_tool, TavilySearchResults(max_results=1)]
        # Re-set up the agent with the new tools
        self.setup_agent()

    def invoke(self, message: str, thread_id: str, user_id: str):
        # Invoke the agent executor with the user's message
        response = self.agent_executor.invoke({"input": message})
        # Return the output from the agent, prioritizing 'output' over 'output_text'
        return response.get("output") or response.get("output_text")


# Main execution block
if __name__ == "__main__":
    # Create a Chatbot instance
    chatbot = Chatbot()