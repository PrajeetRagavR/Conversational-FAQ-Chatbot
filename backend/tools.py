# Import necessary modules
import os
from dotenv import load_dotenv

# Import Tavily search tool
from langchain_tavily import TavilySearch

# Define a function to get the Tavily search tool
def get_tavily_tool():
    """This searches the web for the given query and returns the top 5 results."""
    # Load environment variables from .env file
    load_dotenv()
    # Ensure TAVILY_API_KEY is set in environment variables
    os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")
    # Return a TavilySearchResults instance with a maximum of 5 results
    return TavilySearch(max_results=5)