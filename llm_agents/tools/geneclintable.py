import requests
from llm_agents.tools.base import ToolInterface
from pprint import pprint


class get_gene_clintable(ToolInterface):
    name: str = "get_gene_clintable"
    description: str = (
        "Use this to retrieve comprehensive gene information from the Clinical Tables API based on the given gene symbol or ID. It will return details about the gene, including: GeneID: The unique identifier for a gene. HGNC_ID: The HGNC identifier for the gene, if available in the dbXrefs field. Symbol: The default symbol for the gene. Synonyms: A bar-delimited set of unofficial symbols for the gene. dbXrefs: A bar-delimited set of identifiers in other databases for this gene, formatted as database. chromosome: The chromosome on which this gene is located. 'MT' is used for mitochondrial genomes. map_location: The map location for this gene (cytogenetic location). description: A descriptive name for this gene. type_of_gene: The type assigned to the gene, following the options provided in the NCBI documentation. na_symbol: The symbol from a nomenclature authority. If not '-', it indicates that this symbol is from a nomenclature authority. na_name: The full name from a nomenclature authority. If not '-', it indicates that this full name is from a nomenclature authority. Other_designations: A pipe-delimited set of alternate descriptions assigned to a GeneID. '-' indicates none are reported. Modification_date: The last date a gene record was updated, in YYYYMMDD format. _code_system: Indicates which ID system (e.g., NCBI GeneID, HGNC_ID) is being used for the record. _code: Contains a unique ID of the record based on the 'cf' parameter (specified in the request or default), linked to the _code_system."
        "Input: a valid gene symbol or ID (e.g. BRCA1)"
    )
    url: str = 'https://clinicaltables.nlm.nih.gov/api/ncbi_genes/v3/search'

    def execute_query(self, term: str, max_list: int = 10) -> dict:
        """Executes a query to the Clinical Tables API and returns the data as a dictionary."""
        params = {
            'terms': term,
            'maxList': max_list
        }
        response = requests.get(self.url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def format_gene_info_output(self, data):
        formatted_data = []

        if not data[3]:
            return "No information found for the given gene symbol or ID."

        for item in data[3]:
            gene_info = {
                "Gene ID": item[0],
                "Symbol": item[1],
                "HGNC ID": item[2],
                "Name": item[3],
                "Description": item[4],
                "Type": item[5]
            }
            formatted_data.append(gene_info)

        return formatted_data


    def use(self, input_text: str) -> dict:
        """Fetches and formats gene information from the Clinical Tables API."""
        gene_symbol_or_id = input_text.strip().strip("```")
        try:
            data = self.execute_query(gene_symbol_or_id)
            output = self.format_gene_info_output(data)
            return {"result": output}
        except Exception as e:
            return {"error": str(e)}

if __name__ == '__main__':
    s = get_gene_clintable()
    res = s.use("BRCA1")
    pprint(res)
