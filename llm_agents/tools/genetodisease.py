import requests
import pandas as pd
from llm_agents.tools.base import ToolInterface
import os

class GeneToDisease(ToolInterface):
    name: str = "GeneToDisease"
    description: str = (
        "Use this tool to get the disease associated with a given gene. The databse for this tool is limited, so if you do not find the gene you were looking for in the file, then act as if you never called this tool. Returns a dictionary with the gene as the key, and the value as a list of all the diseases associated with that gene."
        "Input: MUST be a valid gene (e.g. BRCA1)."
    )

    def use(self, input_text: str) -> dict:
        gene = input_text.strip().strip("`").upper()  # Convert input gene to uppercase
        file_path = "/home/groups/mbernst/cs197_data/experiment-data-llm/llm_agents/llm_agents/tools/human_disease_knowledge_filtered.tsv"

        # Check if the file exists
        if not os.path.exists(file_path):
            print(f"File does not exist: {file_path}")
            return {}

        try:
            df = pd.read_csv(file_path, sep='\t', header=None, names=['Column1', 'Gene', 'Column3', 'Disease', 'Column5', 'Column6', 'Column7'])
            print("File read successfully.")  # Debugging statement
            print(df.head())  # Print the first few rows of the DataFrame
        except Exception as e:
            print(f"Failed to read file: {e}")
            return {}

        df['Gene'] = df['Gene'].str.upper()
        filtered_df = df[df['Gene'] == gene]
        print(filtered_df)  # Print the filtered DataFrame
        diseases = filtered_df['Disease'].unique().tolist()
        return {gene: diseases}