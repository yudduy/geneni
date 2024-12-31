import requests
import pandas as pd
from llm_agents.tools.toolinterface import ToolInterface
import os
from pathlib import Path
from pydantic import BaseModel, ConfigDict

class GeneToDisease(ToolInterface):
    name: str = "GeneToDisease"
    description: str = (
        "Use this tool to get the disease associated with a given gene. "
        "Returns a dictionary with the gene as the key, and the value as a list of diseases. "
        "Input: MUST be a valid gene (e.g. BRCA1)."
    )
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    project_root: Path = None
    database_path: str = None

    def __init__(self, **data):
        super().__init__(**data)
        # Initialize paths after parent initialization
        self.project_root = Path(__file__).parent.parent.parent
        self.database_path = os.path.join(self.project_root, "llm_agents", "tools", "human_disease_database.tsv")

    def use(self, input_text: str) -> dict:
        gene = input_text.strip().strip("`").upper()

        if not os.path.exists(self.database_path):
            print(f"Database file not found at: {self.database_path}")
            return {}

        try:
            df = pd.read_csv(self.database_path, sep='\t', 
                           header=None, 
                           names=['Column1', 'Gene', 'Column3', 'Disease', 'Column5', 'Column6', 'Column7'])
            
            df['Gene'] = df['Gene'].str.upper()
            filtered_df = df[df['Gene'] == gene]
            diseases = filtered_df['Disease'].unique().tolist()
            return {gene: diseases}
        except Exception as e:
            print(f"Failed to read database: {e}")
            return {}