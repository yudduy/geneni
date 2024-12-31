from llm_agents import (
    HarmonizomeTool,
    NCBITool,
    OpenTargetsGeneticsAPI,
    EnsemblTool,
    DisGeNETTool
)

def test_all_tools():
    """Test all tools with sample queries."""
    
    tools = [
        (HarmonizomeTool(), ["BRCA1", "breast cancer"]),
        (NCBITool(), ["BRCA1", "rs58991260"]),
        (OpenTargetsGeneticsAPI(), ["rs58991260", "BRCA1"]),
        (EnsemblTool(), ["BRCA1", "rs58991260"]),
        (DisGeNETTool(), ["BRCA1", "breast cancer"])
    ]
    
    for tool, test_queries in tools:
        print(f"\nTesting {tool.name}:")
        for query in test_queries:
            print(f"\nQuery: {query}")
            try:
                result = tool.use(query)
                print(f"Result: {result.get('result', result.get('error', 'No result'))}")
            except Exception as e:
                print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_all_tools() 