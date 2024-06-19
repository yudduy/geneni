import requests
import ToolInterface

class NCBITool(ToolInterface):
    # Example: Retrieve information about the BRCA1 gene from NCBI Gene database
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "gene",
        "term": "BRCA1[gene]",
        "retmode": "json"
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    # Extract gene ID
    gene_id = data['esearchresult']['idlist'][0]

    # Retrieve detailed gene information
    summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    summary_params = {
        "db": "gene",
        "id": gene_id,
        "retmode": "json"
    }

    summary_response = requests.get(summary_url, summary_params)
    gene_info = summary_response.json()

    return(gene_info)