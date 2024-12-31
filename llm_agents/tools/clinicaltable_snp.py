from pydantic import BaseModel, ConfigDict
import requests
from typing import Dict, Any, List
from llm_agents.tools.toolinterface import ToolInterface

class get_snp_clintable(ToolInterface):
    """Clinical Tables API client for SNP information."""
    
    name: str = "get_snp_clintable"
    description: str = (
        "Use this to get SNP information from the Clinical Tables API. "
        "Returns: chromosome location, alleles, and associated genes. "
        "Input: rsID (e.g., rs12345)"
    )
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    base_url: str = 'https://clinicaltables.nlm.nih.gov/api/snps/v3/search'
    
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

    def format_snp_info(self, data: List) -> List[Dict[str, Any]]:
        """Format SNP information into a structured format."""
        formatted_data = []
        
        for item in data[3]:
            snp_info = {
                "rsID": item[0],
                "chromosome": item[1],
                "position": item[2],
                "alleles": item[3],
                "gene": item[4] if len(item) > 4 else None
            }
            formatted_data.append(snp_info)
            
        return formatted_data

    def use(self, input_text: str) -> Dict[str, Any]:
        """Main interface for the tool."""
        try:
            # Clean input
            rsid = input_text.strip().lower()
            if not rsid.startswith('rs'):
                rsid = 'rs' + rsid
                
            # Execute query
            result = self.execute_query(rsid)
            
            if "error" in result:
                return result
                
            # Format response
            formatted_data = self.format_snp_info(result["data"])
            
            return {
                "result": formatted_data,
                "source": "ClinicalTables SNP Database"
            }
            
        except Exception as e:
            return {"error": f"Failed to process SNP information: {str(e)}"}

if __name__ == '__main__':
    s = get_snp_clintable()
    res = s.use("rs12345")
    pprint(res)