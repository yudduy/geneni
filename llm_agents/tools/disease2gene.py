import requests
from llm_agents.tools.base import ToolInterface

class disease2gene(ToolInterface):
    
    name: str = "DiseaseToGene"
    description: str = (
        "Use this tool to get the genes associated with a given disease. Returns a dictionary with the disease as the key, and the value as a list of genes associated with that disease."
        "Input: must be a valid disease name (e.g. breast cancer) separated by a space."
    )
    
    def use(self, input_text: str) -> dict:
        disease = input_text.strip().strip("```")
        genes = []
        
        # Define the root API endpoint URL
        root_url = "https://maayanlab.cloud/Harmonizome/api/1.0/dataset/GWASdb+SNP-Disease+Associations"
        
        # Make a GET request to the root API endpoint
        response = requests.get(root_url)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response from the root endpoint
            data = response.json()
            
            # Extract the list of gene sets
            gene_sets = data.get('geneSets', [])
            
            # Iterate over each gene set to find the matching disease
            for gene_set in gene_sets:
                if disease.lower() in gene_set.get('name', '').lower():
                    # Correctly construct the URL for the specific gene set
                    gene_set_url = "https://maayanlab.cloud/Harmonizome" + gene_set.get('href', '')
                    print(f"Fetching data from: {gene_set_url}")  # Debug statement
                    
                    # Make a GET request to the specific gene set URL
                    gene_set_response = requests.get(gene_set_url)
                    
                    # Check if the request was successful
                    if gene_set_response.status_code == 200:
                        # Parse the JSON response for the specific gene set
                        gene_set_data = gene_set_response.json()
                        
                        # Extract the genes associated with the disease
                        for item in gene_set_data.get('associations', []):
                            gene_symbol = item.get('gene', {}).get('symbol', '')
                            if gene_symbol:
                                genes.append(gene_symbol)
                        break  # Assuming one match is enough, exit loop
                    else:
                        print(f"Failed to retrieve data for {gene_set_url}: {gene_set_response.status_code}")
        else:
            print(f"Failed to retrieve data: {response.status_code}")
        
        result = {'disease': disease, 'genes': genes}
        return result

# Example usage
if __name__ == '__main__':
    disease_to_gene_tool = gene2disease()
    result = disease_to_gene_tool.use("cystic fibrosis")
    print(f"Final answer is {result}")

