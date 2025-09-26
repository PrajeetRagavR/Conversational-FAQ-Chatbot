import os
from typing import List
from langchain_core.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from tools import get_tavily_tool

def get_llm(model_name: str = "gemini-2.5-flash", temperature: float = 0.7, tools: List[BaseTool] = None):
    load_dotenv() # Load environment variables from .env file
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    llm = ChatGoogleGenerativeAI(model=model_name, temperature=temperature, google_api_key=google_api_key)
    tools=[get_tavily_tool()]
    if tools:
        return llm.bind_tools(tools)
    return llm