import sys
import asyncio

# --- FIX FOR WINDOWS ASYNCIO ERRORS ---
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# --------------------------------------

import streamlit as st
import os
# ... rest of your imports ...
import streamlit as st
import asyncio
import os
import sys
import json
from groq import AsyncGroq
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()  # Loads variables from .env

# Check for API Key immediately
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("❌ GROQ_API_KEY not found. Please check your .env file.")
    st.stop()
else:
    # Set it for the Groq client
    os.environ["GROQ_API_KEY"] = api_key

st.set_page_config(page_title="MCP + Groq Demo", layout="centered")
st.title("🤖 MCP Client with Groq")

if "messages" not in st.session_state:
    st.session_state.messages = []

def get_groq_tool_definition(mcp_tool):
    return {
        "type": "function",
        "function": {
            "name": mcp_tool.name,
            "description": mcp_tool.description,
            "parameters": mcp_tool.inputSchema
        }
    }

async def run_chat_loop(user_input):
    # Determine paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(current_dir, "server.py")
    python_exe = sys.executable
    env = os.environ.copy()
    env["PYTHONPATH"] = current_dir

    server_params = StdioServerParameters(
        command=python_exe,
        args=[server_path],
        env=env
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:

                # Initialize
                await session.initialize()

                # List Tools
                tools_result = await session.list_tools()
                groq_tools = [get_groq_tool_definition(tool) for tool in tools_result.tools]

                with st.sidebar:
                    st.success("✅ Connected to MCP Server")
                    st.write("Available Tools:")
                    for t in tools_result.tools:
                        st.code(t.name)

                # Initialize Client
                client = AsyncGroq()

                # Prepare the conversation history
                # System prompt instructions
                system_prompt = {
                    "role": "system",
                    "content": "You are a helpful assistant. You must use the provided tools to answer questions about math, time, or status."
                }

                # Combine system prompt with chat history
                messages_for_api = [system_prompt] + st.session_state.messages

                # --- STEP 1: THINKING (First Call) ---
                response = await client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages_for_api,
                    tools=groq_tools,
                    tool_choice="auto"
                )

                response_message = response.choices[0].message
                tool_calls = response_message.tool_calls

                if tool_calls:
                    # Append the model's thought to the history
                    st.session_state.messages.append(response_message)
                    messages_for_api.append(response_message)

                    for tool_call in tool_calls:
                        fname = tool_call.function.name
                        fargs = json.loads(tool_call.function.arguments)

                        st.sidebar.write(f"⚙️ Calling: {fname}")

                        # Execute Tool via MCP
                        result = await session.call_tool(fname, arguments=fargs)
                        tool_output = result.content[0].text

                        # Append tool result to history
                        tool_message = {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": fname,
                            "content": tool_output,
                        }
                        st.session_state.messages.append(tool_message)
                        messages_for_api.append(tool_message)

                    # --- STEP 2: ANSWERING (Second Call) ---
                    final_response = await client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=messages_for_api
                    )
                    return final_response.choices[0].message.content

                else:
                    # No tool was needed
                    return response_message.content

    except Exception as e:
        return f"❌ Error: {str(e)}"

# --- UI LOGIC ---
for message in st.session_state.messages:
    if isinstance(message, dict):
        role = message["role"]
        if role in ["user", "assistant"]:
            with st.chat_message(role):
                st.markdown(message["content"])

if prompt := st.chat_input("Ask about time, math, or system status..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Connecting to tools..."):
            response_text = asyncio.run(run_chat_loop(prompt))
            st.markdown(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response_text})