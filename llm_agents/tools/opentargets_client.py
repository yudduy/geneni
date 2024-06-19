import requests
from llm_agents.tools.base import ToolInterface
from pprint import pprint

class OpenTargetsClient(ToolInterface):
    name: str = "opentargets_client"
    description: str = (
        "Use this to get gene-disease associations from the Open Targets Genetics API. "
        "It will return details about the diseases associated with a given gene symbol or ID."
    )
    api_host: str = 'https://api.genetics.opentargets.org/graphql'

    def execute_query(self, gene_id: str) -> dict:
        """Executes a query to the Open Targets Genetics API and returns the data as a dictionary."""
        query_string = """
        query geneAssociations($geneId: String!) {
            geneInfo(geneId: $geneId) {
                id
                associatedDiseases {
                    score
                    disease {
                        id
                        name
                    }
                }
            }
        }
        """
        variables = {"geneId": gene_id}
        headers = {"Content-Type": "application/json"}
        print(f"Request URL: {self.api_host}")
        print(f"Request Headers: {headers}")
        print(f"Query: {query_string}")
        print(f"Variables: {variables}")
        try:
            response = requests.post(self.api_host, json={"query": query_string, "variables": variables}, headers=headers)
            response.raise_for_status()  # Raise an error for bad response codes
            # Check if the response is JSON
            if response.headers.get('Content-Type') == 'application/json':
                return response.json()
            else:
                print(f"Unexpected content type: {response.headers.get('Content-Type')}")
                print(f"Response content: {response.content}")
                return {"error": "Unexpected response format"}
        except requests.RequestException as e:
            print(f"Request failed for {self.api_host}: {e}")
            print(f"Response content: {response.content if response else 'No response'}")
            return {"error": "Failed to retrieve data from the API."}

    def format_gene_disease_output(self, data):
        if not data or not data.get('data') or not data['data'].get('geneInfo'):
            return "No associations found for the given gene ID."

        formatted_data = []
        for assoc in data['data']['geneInfo']['associatedDiseases']:
            disease_info = {
                "Disease": assoc.get('disease', {}).get('name', 'N/A'),
                "ID": assoc.get('disease', {}).get('id', 'N/A'),
                "Score": assoc.get('score', 'N/A')
            }
            formatted_data.append(disease_info)

        return formatted_data

    def get_associations(self, gene_id: str) -> dict:
        """Fetches and formats gene-disease associations from the Open Targets Genetics API."""
        data = self.execute_query(gene_id)
        if data is None or "error" in data:
            return {"error": "Failed to retrieve data from the API."}
        output = self.format_gene_disease_output(data)
        return {"result": output}

    def use(self, input_text: str) -> dict:
        """Implements the use method required by the ToolInterface."""
        gene_id = input_text.strip()
        return self.get_associations(gene_id)

if __name__ == '__main__':
    client = OpenTargetsClient()
    res = client.use("ENSG00000139618")  # Example gene ID for BRCA2
    pprint(res)
