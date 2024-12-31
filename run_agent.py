import os
import sys
from llm_agents.tools.toolinterface import ToolInterface
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
    GeneToDisease,
    DisGeNETClient
)

def create_agent():
    """Create and initialize the agent with properly configured tools."""
    try:
        # Initialize LLM first
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
        
        # Create agent with configured tools
        return Agent(llm=llm, tools=tools)
    except Exception as e:
        print(f"Error initializing agent: {str(e)}")
        raise

def run_cli():
    """Run the command-line interface."""
    try:
        agent = create_agent()
        print("\nAgent initialized successfully!")
        
        while True:
            try:
                prompt = input("\nEnter a question / task for the agent (or 'quit' to exit): ")
                if prompt.lower() in ['quit', 'exit', 'q']:
                    break
                    
                print("\nProcessing your question...")
                
                result = agent.run(prompt)
                
                if result:
                    print("\nFinal answer:", result)
                else:
                    print("\nNo answer was provided.")
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"\nError processing query: {str(e)}")
    
    except Exception as e:
        print(f"Failed to initialize agent: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    run_cli()
    