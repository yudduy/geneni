import os
from llm_agents.llm import ChatLLM

def test_llm():
    try:
        llm = ChatLLM()
        
        response = llm.generate("What is DNA?")
        print("Test successful!")
        print("Response:", response)
        
    except Exception as e:
        print("Test failed:", str(e))

if __name__ == "__main__":
    if not os.getenv('GOOGLE_API_KEY'):
        print("Error: GOOGLE_API_KEY environment variable not set")
        exit(1)
        
    test_llm()