from pydantic import BaseModel, ConfigDict
import requests
from typing import Dict, Any, List
from llm_agents.tools.toolinterface import ToolInterface

class get_gene_clintable(ToolInterface):
    """Clinical Tables API client for gene information."""
    
    name: str = "get_gene_clintable"
    description: str = (
        "Use this to retrieve gene information from the Clinical Tables API. "
        "Returns: gene details including ID, symbol, name, and description. "
        "Input: gene symbol (e.g., BRCA1)"
    )
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    base_url: str = 'https://clinicaltables.nlm.nih.gov/api/ncbi_genes/v3/search'
    
    def __init__(self, **data):
        super().__init__(**data)
        self._session = requests.Session()

    def execute_query(self, term: str, max_list: int = 10) -> Dict[str, Any]:
        """Execute query with proper error handling."""
        try:
            params = {
                'terms': term,
                'maxList': max_list
            }
            response = self._session.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data or len(data) < 4 or not data[3]:
                return {"error": f"No information found for {term}"}
                
            return {"data": data}
            
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}

    def format_gene_info(self, data: List) -> List[Dict[str, Any]]:
        """Format gene information into a structured format."""
        formatted_data = []
        
        for item in data[3]:
            gene_info = {
                "Gene ID": item[0],
                "Symbol": item[1],
                "HGNC ID": item[2],
                "Name": item[3],
                "Description": item[4],
                "Type": item[5] if len(item) > 5 else None
            }
            formatted_data.append(gene_info)
            
        return formatted_data

    def use(self, input_text: str) -> Dict[str, Any]:
        """Main interface for the tool."""
        try:
            # Clean input
            gene_symbol = input_text.strip().upper()
            
            # Execute query
            result = self.execute_query(gene_symbol)
            
            if "error" in result:
                return result
                
            # Format response
            formatted_data = self.format_gene_info(result["data"])
            
            return {
                "result": formatted_data,
                "source": "ClinicalTables Gene Database"
            }
            
        except Exception as e:
            return {"error": f"Failed to process gene information: {str(e)}"}
