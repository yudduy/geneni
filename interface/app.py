import streamlit as st
import sys
import os
from pathlib import Path

# Add parent directory to path to import llm_agents
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

st.set_page_config(page_title="Geneni: Biological Agent", layout="wide")

def create_agent():
    """Create and initialize the agent with all necessary tools."""
    try:
        # Initialize LLM
        llm = ChatLLM()
        
        # Initialize tools
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
        
        # Create agent
        return Agent(llm=llm, tools=tools)
    except Exception as e:
        st.error(f"Failed to initialize agent: {str(e)}")
        return None

def initialize_session_state():
    """Initialize or reset the session state."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Initialize agent if not already present or if it failed
    if "agent" not in st.session_state or st.session_state.agent is None:
        st.session_state.agent = create_agent()
        if st.session_state.agent is None:
            st.error("Failed to initialize the agent. Please refresh the page.")
            return False
    return True

def main():
    st.title("Geneni: Biological Database Assistant")
    
    if not initialize_session_state():
        return
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Generate response
        with st.chat_message("assistant"):
            try:
                with st.spinner("Thinking..."):
                    # Create expandable section for thought process
                    with st.expander("View thinking process", expanded=False):
                        thought_container = st.empty()
                        
                        def update_thoughts(text):
                            current_thoughts = thought_container.text
                            if current_thoughts:
                                thought_container.markdown(f"{current_thoughts}\n\n{text}")
                            else:
                                thought_container.markdown(text)
                        
                        # Override the input function for verification prompt
                        def mock_input():
                            verify_container = st.empty()
                            result = verify_container.radio(
                                "Would you like me to verify this information using biological databases?",
                                ["Yes", "No"],
                                index=0
                            ) == "Yes"
                            verify_container.empty()
                            return "yes" if result else "no"
                        
                        # Add callbacks to agent
                        st.session_state.agent.thought_callback = update_thoughts
                        st.session_state.agent._input_func = mock_input
                        
                        response = st.session_state.agent.run(prompt)
                    
                    # Show final response
                    if response:
                        if response.startswith("An error occurred:"):
                            st.error(response)
                        else:
                            st.markdown(response)
                        
                        st.session_state.messages.append(
                            {"role": "assistant", "content": response}
                        )
                    else:
                        st.error("No response generated")
                        
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 