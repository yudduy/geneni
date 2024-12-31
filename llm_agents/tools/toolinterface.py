from pydantic import BaseModel, ConfigDict
from typing import Dict, Any

class ToolInterface(BaseModel):
    """Base interface for all tools."""
    
    name: str
    description: str
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def use(self, input_text: str) -> Dict[str, Any]:
        """Execute the tool with the given input."""
        raise NotImplementedError("Tool must implement use method")
