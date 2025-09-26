import os
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, MessagesState, END, START
from trustcall import create_extractor

from llm import get_llm
from schema import UserProfile, get_across_thread_memory, get_within_thread_memory
from tools import get_tavily_tool
from rag.rag import load_documents, split_documents, create_vector_store, get_retriever

# Set up Google Generative AI
# Ensure GOOGLE_API_KEY is set in your environment variables
# os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY"

tools = [get_tavily_tool()]
model = get_llm(tools=tools)
model_with_structure = get_llm().with_structured_output(UserProfile)

CREATE_MEMORY_INSTRUCTION = """Create or update a user profile memory based on the user's chat history. \
This will be saved for long-term memory. If there is an existing memory, simply update it. \
Here is the existing memory (it may be empty): {memory}"""

MODEL_SYSTEM_MESSAGE = """You are a helpful assistant with memory that provides information about the user. And answers the user query based on the knowledge base, if the answer is not in the documents then use the tavily search tool to fetch answers from the internet and display the results. \
If you have memory for this user, use it to personalize your responses. \
Here is the memory (it may be empty): {memory}"""

class Chatbot:
    def __init__(self):
        self.builder = StateGraph(MessagesState)
        self.builder.add_node("chatbot", self.call_model)
        self.builder.add_node("write_memory", self.write_memory)
        self.builder.set_entry_point("chatbot")
        self.builder.add_edge("chatbot", "write_memory")
        self.builder.add_edge("write_memory", END)

        self.across_thread_memory = get_across_thread_memory()
        self.within_thread_memory = get_within_thread_memory()

        self.graph = self.builder.compile(
            checkpointer=self.within_thread_memory,
            store=self.across_thread_memory
        )

        self.retriever = None # Initialize retriever as None

    def set_retriever(self, retriever):
        self.retriever = retriever

    def _generate_similar_queries(self, original_query: str) -> list[str]:
        prompt = f"""Generate 3 similar search queries based on the following query. 
        The queries should be designed to catch potential spelling errors or alternative phrasings.
        Return them as a comma-separated list.

        Original query: {original_query}
        Similar queries:"""
        response = model.invoke([HumanMessage(content=prompt)])
        return [q.strip() for q in response.content.split(',') if q.strip()]

    def call_model(self, state: MessagesState, config: RunnableConfig):
        user_id = config["configurable"]["user_id"]
        namespace = ("memory", user_id)
        existing_memory = self.across_thread_memory.get(namespace, "user_memory")

        formatted_memory = None
        if existing_memory and existing_memory.value:
            memory_dict = existing_memory.value
            formatted_memory = (
                f"Name: {memory_dict.get('user_name', 'Unknown')}\\n"
                f"Location: {memory_dict.get('user_location', 'Unknown')}\\n"
                f"Interests: {', '.join(memory_dict.get('interests', []))}"
            )

        system_msg = MODEL_SYSTEM_MESSAGE.format(memory=formatted_memory)

        # Extract the latest user message
        user_message_content = None
        for message in reversed(state["messages"]):
            if isinstance(message, HumanMessage):
                user_message_content = message.content
                break

        search_message_content = []

        if user_message_content:
            # Use RAG to retrieve relevant documents if retriever is available
            if self.retriever:
                retrieved_docs = self.retriever.invoke(user_message_content)
                retrieved_content = "\n\nRelevant Documents:\n" + "\n".join([doc.page_content for doc in retrieved_docs])
                search_message_content.append(retrieved_content)

            # Generate similar queries
            similar_queries = self._generate_similar_queries(user_message_content)
            all_queries = [user_message_content] + similar_queries

            # Use Tavily tool with all queries
            tavily_tool = tools[0] # Assuming Tavily is the first tool
            search_results = []
            for query in all_queries:
                try:
                    result = tavily_tool.invoke({"query": query})
                    search_results.append(f"Query: {query}\nResult: {result}")
                except Exception as e:
                    search_results.append(f"Query: {query}\nError: {e}")
            search_message_content.append("\n".join(search_results))

            # Add search results and retrieved documents to the messages for the LLM to consider
            search_message = SystemMessage(content="\n".join(search_message_content))
            response = model.invoke([SystemMessage(content=system_msg), search_message] + state["messages"])
        else:
            response = model.invoke([SystemMessage(content=system_msg)] + state["messages"])

        return {"messages": [response]}

    def write_memory(self, state: MessagesState, config: RunnableConfig):
        user_id = config["configurable"]["user_id"]
        namespace = ("memory", user_id)
        existing_memory = self.across_thread_memory.get(namespace, "user_memory")

        formatted_memory = None
        if existing_memory and existing_memory.value:
            memory_dict = existing_memory.value
            formatted_memory = (
                f"Name: {memory_dict.get('user_name', 'Unknown')}\\n"
                f"Location: {memory_dict.get('user_location', 'Unknown')}\\n"
                f"Interests: {', '.join(memory_dict.get('interests', []))}"
            )

        system_msg = CREATE_MEMORY_INSTRUCTION.format(memory=formatted_memory)
        new_memory = model_with_structure.invoke([SystemMessage(content=system_msg)] + state["messages"])

        key = "user_memory"
        self.across_thread_memory.put(namespace, key, new_memory.model_dump())
        return state

    def invoke(self, message: str, thread_id: str, user_id: str):
        # Ensure user_id is treated as a string (UUID from database will be converted to string)
        user_id = str(user_id)
        config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}
        response = self.graph.invoke({"messages": [HumanMessage(content=message)]}, config)
        llm_response = response["messages"][-1].content
        print(f"LLM Response: {llm_response}") # Add this line to print the LLM response
        return llm_response

if __name__ == "__main__":
    # Example usage
    chatbot = Chatbot()

    # First conversation
    print("User 1, Thread 1:")
    response = chatbot.invoke("Hi, my name is Alice. I live in New York and I like reading and hiking.", "thread_1", "user_1")
    print(f"Chatbot: {response}")

    response = chatbot.invoke("What is the capital of France?", "thread_1", "user_1")
    print(f"Chatbot: {response}")

    response = chatbot.invoke("Do you remember my name and where I live?", "thread_1", "user_1")
    print(f"Chatbot: {response}")

    # Second conversation (different user, different thread)
    print("\nUser 2, Thread 2:")
    response = chatbot.invoke("Hello, I'm Bob. I like to hike and play guitar. I'm from California.", "thread_2", "user_2")
    print(f"Chatbot: {response}")

    response = chatbot.invoke("What are some good hiking trails near mountains?", "thread_2", "user_2")
    print(f"Chatbot: {response}")

    response = chatbot.invoke("Do you remember my name and what I like?", "thread_2", "user_2")
    print(f"Chatbot: {response}")
