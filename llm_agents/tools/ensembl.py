"""
Ensembl REST API client for retrieving gene and variant information.
"""

import sys
import json
import time
import requests
from typing import Dict, Any, Optional
from llm_agents.tools.toolinterface import ToolInterface
from pydantic import BaseModel, ConfigDict

class EnsemblTool(ToolInterface):
    """Tool for querying the Ensembl REST API."""
    
    name: str = "EnsemblTool"
    description: str = (
        "Use this tool to query Ensembl database for genomic information. "
        "Input can be:\n"
        "1. A variant ID (e.g., 'rs699')\n"
        "2. A gene symbol (e.g., 'BRCA1')\n"
        "Returns genomic coordinates, annotations, and variant information."
    )
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    base_url: str = 'https://rest.ensembl.org'
    
    def __init__(self, **data):
        super().__init__(**data)
        self._session = requests.Session()
        self._session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'EnsemblClient/1.0'
        })

    def query_variant(self, variant_id: str) -> Dict[str, Any]:
        """Query information about a specific variant."""
        try:
            url = f"{self.base_url}/variation/human/{variant_id}"
            response = self._session.get(url)
            response.raise_for_status()
            return {"result": response.json()}
        except Exception as e:
            return {"error": f"Failed to query variant {variant_id}: {str(e)}"}

    def query_gene(self, gene_symbol: str) -> Dict[str, Any]:
        """Query information about a specific gene."""
        try:
            # First lookup gene ID
            lookup_url = f"{self.base_url}/lookup/symbol/homo_sapiens/{gene_symbol}"
            response = self._session.get(lookup_url)
            response.raise_for_status()
            gene_data = response.json()
            
            # Get detailed information
            gene_id = gene_data.get('id')
            if not gene_id:
                return {"error": f"Gene {gene_symbol} not found"}
                
            detail_url = f"{self.base_url}/lookup/id/{gene_id}"
            detail_response = self._session.get(detail_url)
            detail_response.raise_for_status()
            
            return {"result": detail_response.json()}
        except Exception as e:
            return {"error": f"Failed to query gene {gene_symbol}: {str(e)}"}

    def use(self, input_text: str) -> Dict[str, Any]:
        """Main interface that handles both variant and gene queries."""
        query = input_text.strip()
        
        if query.lower().startswith('rs'):
            return self.query_variant(query)
        else:
            return self.query_gene(query)

# For backward compatibility
def ensembl_rest_client(server: str = "https://rest.ensembl.org"):
    """Deprecated: Use EnsemblTool class instead."""
    return EnsemblTool()

if __name__ == '__main__':
    tool = EnsemblTool()
    
    # Test variant query
    variant_result = tool.use("rs699")
    print("Variant query result:", variant_result)
    
    # Test gene query
    gene_result = tool.use("BRCA1")
    print("Gene query result:", gene_result) 