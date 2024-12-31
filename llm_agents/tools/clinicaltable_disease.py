from pydantic import BaseModel, ConfigDict
import requests
from typing import Dict, Any, List
from llm_agents.tools.toolinterface import ToolInterface

class get_disease_clintable(ToolInterface):
    """Clinical Tables API client for disease information."""
    
    name: str = "get_disease_clintable"
    description: str = (
        "Use this to get disease information from the Clinical Tables API. "
        "Returns: disease names and related details. "
        "Input: disease name (e.g., diabetes)"
    )
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    base_url: str = 'https://clinicaltables.nlm.nih.gov/api/conditions/v3/search'
    
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

    def format_disease_info(self, data: List) -> List[Dict[str, Any]]:
        """Format disease information into a structured format."""
        formatted_data = []
        
        for idx, name in enumerate(data[1]):
            disease_info = {
                "name": name,
                "details": data[3][idx] if len(data) > 3 and idx < len(data[3]) else None
            }
            formatted_data.append(disease_info)
            
        return formatted_data

    def use(self, input_text: str) -> Dict[str, Any]:
        """Main interface for the tool."""
        try:
            # Clean input
            disease_term = input_text.strip()
            
            # Execute query
            result = self.execute_query(disease_term)
            
            if "error" in result:
                return result
                
            # Format response
            formatted_data = self.format_disease_info(result["data"])
            
            return {
                "result": formatted_data,
                "source": "ClinicalTables Disease Database"
            }
            
        except Exception as e:
            return {"error": f"Failed to process disease information: {str(e)}"}

if __name__ == '__main__':
    s = get_disease_clintable()
    res = s.use("cystic fibrosis")
    pprint(res)

