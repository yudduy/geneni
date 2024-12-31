from pydantic import BaseModel, ConfigDict
import requests
from typing import Dict, Any, Optional
from llm_agents.tools.toolinterface import ToolInterface

class NCBITool(ToolInterface):
    """Tool for interacting with NCBI APIs."""
    
    name: str = "NCBITool"
    description: str = "Tool for querying NCBI databases for gene and SNP information"
    base_url: str = 'https://api.ncbi.nlm.nih.gov'
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, **data):
        super().__init__(**data)
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; GeneniBot/1.0)',
        })

    def search_gene(self, gene_symbol: str) -> Dict[str, Any]:
        """Search for gene information."""
        try:
            search_params = {
                "db": "gene",
                "term": f"{gene_symbol}[Gene Name] AND human[Organism]",
                "retmode": "json"
            }
            
            response = self._session.get(f"{self.base_url}/esearch.fcgi", params=search_params)
            response.raise_for_status()
            search_data = response.json()
            
            if not search_data['esearchresult'].get('idlist'):
                return {"error": f"No gene found for symbol: {gene_symbol}"}
            
            gene_id = search_data['esearchresult']['idlist'][0]
            
            summary_params = {
                "db": "gene",
                "id": gene_id,
                "retmode": "json"
            }
            
            response = self._session.get(f"{self.base_url}/esummary.fcgi", params=summary_params)
            response.raise_for_status()
            
            return {"result": response.json()}
            
        except Exception as e:
            return {"error": f"NCBI API request failed: {str(e)}"}

    def search_snp(self, rs_id: str) -> Dict[str, Any]:
        """Search for SNP information."""
        try:
            search_params = {
                "db": "snp",
                "term": f"{rs_id}[RS]",
                "retmode": "json"
            }
            
            response = self._session.get(f"{self.base_url}/esearch.fcgi", params=search_params)
            response.raise_for_status()
            search_data = response.json()
            
            if not search_data['esearchresult'].get('idlist'):
                return {"error": f"No SNP found for: {rs_id}"}
            
            snp_id = search_data['esearchresult']['idlist'][0]
            
            summary_params = {
                "db": "snp",
                "id": snp_id,
                "retmode": "json"
            }
            
            response = self._session.get(f"{self.base_url}/esummary.fcgi", params=summary_params)
            response.raise_for_status()
            
            return {"result": response.json()}
            
        except Exception as e:
            return {"error": f"NCBI API request failed: {str(e)}"}

    def use(self, input_text: str) -> Dict[str, Any]:
        """Main interface for the tool."""
        query = input_text.strip().upper()
        
        if query.startswith('RS'):
            return self.search_snp(query)
        else:
            return self.search_gene(query)

if __name__ == '__main__':
    tool = NCBITool()
    result = tool.use("BRCA1")
    print(result)