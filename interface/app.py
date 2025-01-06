import streamlit as st
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from llm_agents import (
    Agent, 
    ChatLLM,
    HarmonizomeTool,
    NCBITool,
    OpenTargetsGeneticsAPI, 
    get_snp_clintable, 
    get_gene_clintable, 
    EnsemblTool, 
    get_disease_clintable, 
    GeneToDisease
)

# Configure page
st.set_page_config(
    page_title="Geneni: Biological Agent",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent" not in st.session_state:
    st.session_state.agent = None
if "api_key" not in st.session_state:
    st.session_state.api_key = None
if "initialized" not in st.session_state:
    st.session_state.initialized = False

def create_agent(api_key: str):
    """Create agent with provided API key."""
    try:
        os.environ['GOOGLE_API_KEY'] = api_key
        llm = ChatLLM()
        tools = [
            EnsemblTool(),
            NCBITool(),
            get_snp_clintable(),
            OpenTargetsGeneticsAPI(),
            GeneToDisease(),
            get_gene_clintable(),
            get_disease_clintable(),
            HarmonizomeTool()
        ]
        return Agent(llm=llm, tools=tools)
    except Exception as e:
        st.error(f"Failed to initialize agent: {str(e)}")
        return None

def main():
    st.title("Geneni: Biological Database Assistant")
    
    # API Key input and agent initialization
    if not st.session_state.initialized:
        with st.form("api_key_form"):
            api_key = st.text_input(
                "Please enter your Google Cloud API key:",
                type="password",
                help="Your API key will not be stored permanently"
            )
            submitted = st.form_submit_button("Initialize Agent")
            
            if submitted and api_key:
                st.session_state.api_key = api_key
                with st.spinner("Initializing agent..."):
                    st.session_state.agent = create_agent(api_key)
                    if st.session_state.agent is not None:
                        st.session_state.initialized = True
                        st.success("Agent initialized successfully!")
            elif submitted:
                st.error("Please provide an API key")
        
        if not st.session_state.initialized:
            return

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask me anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                thoughts = []
                def update_thoughts(text):
                    thoughts.append(text)
                    with st.expander("View thinking process", expanded=False):
                        st.markdown("\n\n".join(thoughts))

                def mock_input():
                    verify_col = st.empty()
                    with verify_col:
                        result = st.radio(
                            "Would you like me to verify this information using biological databases?",
                            ["Yes", "No"],
                            key=f"verify_{len(st.session_state.messages)}"
                        )
                    return "yes" if result == "Yes" else "no"

                st.session_state.agent.thought_callback = update_thoughts
                st.session_state.agent._input_func = mock_input

                with st.spinner("Processing..."):
                    response = st.session_state.agent.run(prompt)

                if response:
                    st.markdown(response)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response
                    })
                else:
                    st.error("No response generated")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                if "invalid api key" in str(e).lower():
                    st.session_state.agent = None
                    st.session_state.api_key = None
                    st.session_state.initialized = False
                    st.error("Invalid API key. Please try again with a valid key.")
                    st.rerun()

    # Add a way to reset the API key if needed
    if st.sidebar.button("Reset API Key"):
        st.session_state.agent = None
        st.session_state.api_key = None
        st.session_state.initialized = False
        st.rerun()

if __name__ == "__main__":
    main() 