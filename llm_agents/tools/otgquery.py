from llm_agents.tools.base import ToolInterface

#!/usr/bin/env python3

# Import relevant libraries for HTTP request and JSON formatting
import requests
import json

class otg_graphql(ToolInterface):

    name: str = "Open Target Genetics API (Target Query)"
    description: str = "Tool to query the Open Target Genetics API using GraphQL (target endpoint)"

    def use(self, input_text: str):
        # Set the target ID
        target_id = "ENSG00000157764"  # Example target ID
        
        # Build the GraphQL query string for querying target data
        query_string = """
            query getTarget($targetId: String!) {
                target(targetId: $targetId) {
                    id
                    symbol
                    name
                    description
                    biotype
                    approvedSymbol
                    approvedName
                    externalReferences {
                        datasourceName
                        id
                        url
                    }
                }
            }
        """

        # Set the variables for the GraphQL query
        variables = {"targetId": target_id}

        # Set the base URL of the Open Target Genetics GraphQL API
        base_url = "https://api.genetics.opentargets.org/graphql"

        try:
            # Perform the POST request to the API
            response = requests.post(base_url, json={"query": query_string, "variables": variables})
            response.raise_for_status()  # Raise an error for bad response codes
            api_response_as_json = response.json()

            # Check if the response contains data
            if "data" in api_response_as_json:
                return api_response_as_json["data"]["target"]
            else:
                return "No data in response"
        except requests.RequestException as e:
            return f"Request failed: {e}"
        except json.JSONDecodeError as e:
            return f"Failed to parse JSON: {e}"


#------------------------------------------------------------------------------------------------------------

# functions and class for the QTL variants in the OTG database
def to_hg38_build(rs_id, build='GRCh38') -> dict:
    """Fetches the position of a SNP from the Ensembl REST API for a given build."""
    url = f"https://rest.ensembl.org/variation/human/{rs_id}?content-type=application/json"    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()        
        mappings = data.get('mappings', [])
        for mapping in mappings:
            if mapping.get('assembly_name') == build:
                return {
                    'chromosome': mapping['seq_region_name'],
                    'start': mapping['start'],
                    'end': mapping['end'],
                    'allele_string': mapping['allele_string'],
                    'strand': mapping['strand'],
                    'assembly_name': mapping['assembly_name']
                }
        return "SNP position not found for the specified build."
    except requests.RequestException as e:
        return f"Error fetching SNP position: {e}"

class get_variant_to_QTLs_opentarget(ToolInterface):
    """A tool for getting comprehensive variant-to-gene link information from the Open Targets Genetics API using GraphQL."""

    name: str = "get_variant_to_QTLs_opentarget"
    description: str = (
        "Use this to get QTLs linking to this variant. It will be a list of genes and each gene also has information about the tissue context, QTL type, association level measured by p-value, beta, quantile. "
        "Input: must be a valid rs ID (e.g. rs58991260)"
    )
    url: str = 'https://api.genetics.opentargets.org/graphql'

    def execute_graphql_query(self, query: str, variables: dict) -> dict:
        """Executes a GraphQL query with variables and returns the data as a dictionary."""
        headers = {'Content-Type': 'application/json'}
        response = requests.post(self.url, json={'query': query, 'variables': variables}, headers=headers)
        response.raise_for_status()
        return response.json()

    def format_variant_to_gene_output(self, data):
        formatted_str = ""

        # Basic gene and variant information
        gene_info = data['gene']
        formatted_str += f"Gene ID: {gene_info['id']}, Symbol: {gene_info['symbol']}\n"

        # Iterate over qtls, pqtl, and sqtl
        for qtl in data['qtls']:
            formatted_str += f"QTL Type: {qtl['typeId']}\n"
            for tissue in qtl['tissues']:
                tissue_info = tissue['tissue']
                formatted_str += f"  Tissue: {tissue_info['name']} (ID: {tissue_info['id']})\n"
                formatted_str += f"    Quantile: {tissue['quantile']}\n"
                formatted_str += f"    Beta: {tissue['beta']}\n"
                formatted_str += f"    P-Value: {tissue['pval']:.2e}\n"
            formatted_str += "\n"

        return formatted_str

    def use(self, input_text: str) -> dict:
        """Constructs and executes a query to fetch detailed variant-to-gene link information."""
        variantId = input_text.strip().strip("```")
        position_info = to_hg38_build(variantId)
        print(f"-------\nposition info: {position_info} \n---------\n")

        if not isinstance(position_info, dict):
            return {"error": position_info}  # Return the error message if position_info is not a dict

        try:
            chromosome = position_info['chromosome']
            start = str(position_info['start'])
            allele_string = position_info['allele_string']
            alleles = allele_string.split('/')
            ref_allele = alleles[0]
            alt_alleles = alleles[1:]  # Consider all alternative alleles

            # Create multiple queries for each alt allele if multi-allelic
            results = []
            for alt_allele in alt_alleles:
                variant_id = '_'.join([chromosome, start, ref_allele, alt_allele])
                query = """
                    query getVariantToGeneLinks($variantId: String!) {
                        genesForVariant(variantId: $variantId) {
                            gene {
                                id
                                symbol
                            }
                            qtls {
                                typeId
                                tissues {
                                    tissue {
                                        id
                                        name
                                    }
                                    quantile
                                    beta
                                    pval
                                }
                            }
                        }
                    }
                """
                variables = {"variantId": variant_id}

                try:
                    data = self.execute_graphql_query(query, variables)
                    if len(data['data']['genesForVariant']) == 0:
                        results.append('This variant does not have any QTL information in open target genetics!')
                    else:
                        for gene in data['data']['genesForVariant']:
                            if len(gene['qtls']) > 0:
                                results.append(self.format_variant_to_gene_output(gene))
                except Exception as e:
                    results.append({"error": str(e)})

            return '\n\n'.join(results)
        except KeyError as e:
            return {"error": f"Missing key in position info: {e}"}
        except ValueError as e:
            return {"error": f"Error parsing allele string: {e}"}

if __name__ == '__main__':
    s = get_variant_to_QTLs_opentarget()
    res = s.use("rs58991260")
    print(res)
    
    s = otg_graphql()
    res = s.use("ENSG00000157764")
    print(res)