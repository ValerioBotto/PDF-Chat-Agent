#Agente ReAct con memoria e tool esterni per PDF e web search

from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from langchain_together import ChatTogether
from dotenv import load_dotenv
from agent.tools import get_all_tools  
import os

load_dotenv()

# Funzione per costruire l'agente ReAct con memoria
def build_agent(retriever):
    memory = MemorySaver()

    llm = ChatTogether(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        temperature=0.3,
        together_api_key=os.getenv("TOGETHER_API_KEY")
    )

    tools = get_all_tools(retriever, llm)

    agent = create_react_agent(
        model=llm,
        checkpointer=memory,
        tools=tools
    )
    return agent

# Funzione di invocazione
def invoke_agent(agent, message: str, session_id: str = "default") -> str:
    response = agent.invoke(
        {"messages": [HumanMessage(content=message)]},
        config={"configurable": {
            "session_id": session_id,
            "thread_id": session_id,
            "recursion_limit": 2,
        }}
    )
    return response["messages"][-1].content
