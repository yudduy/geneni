from pydantic import BaseModel, ConfigDict
import requests
from typing import Dict, Any, Optional
from llm_agents.tools.toolinterface import ToolInterface

class HarmonizomeTool(ToolInterface):
    """Unified tool for querying Harmonizome database for gene-disease relationships."""
    
    name: str = "Harmonizome"
    description: str = (
        "Use this tool to query relationships between genes and diseases. "
        "Input can be either:\n"
        "1. A gene symbol (e.g., 'BRCA1') to find associated diseases\n"
        "2. A disease name (e.g., 'breast cancer') to find associated genes\n"
        "Returns comprehensive information about gene-disease associations."
    )
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    base_url: str = "https://maayanlab.cloud/Harmonizome/api/1.0"
    
    def __init__(self, **data):
        super().__init__(**data)
        self._session = requests.Session()
        self._session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'HarmonizomeClient/1.0'
        })

    def search_by_gene(self, gene_symbol: str) -> Dict[str, Any]:
        """Search for diseases and annotations associated with a gene."""
        try:
            url = f"{self.base_url}/gene/{gene_symbol}"
            response = self._session.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Also get gene set associations
            sets_url = f"{self.base_url}/gene/{gene_symbol}/associations"
            sets_response = self._session.get(sets_url)
            sets_response.raise_for_status()
            
            return {
                "result": {
                    "gene_info": data,
                    "associations": sets_response.json()
                }
            }
        except Exception as e:
            return {"error": f"Failed to query gene {gene_symbol}: {str(e)}"}

    def search_by_disease(self, disease: str) -> Dict[str, Any]:
        """Search for genes associated with a disease."""
        try:
            # Search in disease datasets
            url = f"{self.base_url}/dataset/GWASdb+SNP-Disease+Associations/gene_set/{disease}"
            response = self._session.get(url)
            response.raise_for_status()
            
            # Also search DisGeNET dataset
            disgenet_url = f"{self.base_url}/dataset/DisGeNET/gene_set/{disease}"
            disgenet_response = self._session.get(disgenet_url)
            
            results = {
                "gwas_associations": response.json(),
                "disgenet_associations": disgenet_response.json() if disgenet_response.status_code == 200 else None
            }
            
            return {"result": results}
        except Exception as e:
            return {"error": f"Failed to query disease {disease}: {str(e)}"}

    def use(self, input_text: str) -> Dict[str, Any]:
        """Main interface that handles both gene and disease queries."""
        query = input_text.strip()
        
        # Try to determine if input is a gene symbol or disease name
        if len(query.split()) == 1 and query.isupper():  # Likely a gene symbol
            return self.search_by_gene(query)
        else:  # Likely a disease name
            return self.search_by_disease(query)

if __name__ == '__main__':
    tool = HarmonizomeTool()
    
    # Test gene query
    gene_result = tool.use("BRCA1")
    print("Gene query result:", gene_result)
    
    # Test disease query
    disease_result = tool.use("breast cancer")
    print("Disease query result:", disease_result) 