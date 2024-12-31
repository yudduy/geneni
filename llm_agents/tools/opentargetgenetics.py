from pydantic import BaseModel, ConfigDict
import requests
from typing import Dict, Any, Optional
from llm_agents.tools.toolinterface import ToolInterface

class OpenTargetsGeneticsAPI(ToolInterface):
    """Tool for querying Open Targets Genetics API."""
    
    name: str = "OpenTargetsGenetics"
    description: str = (
        "Use this tool to query genetic associations and variants from Open Targets Genetics. "
        "Input can be:\n"
        "1. A variant ID (e.g., 'rs58991260')\n"
        "2. A gene symbol (e.g., 'BRCA1')\n"
        "Returns genetic associations, QTLs, and variant information."
    )
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    base_url: str = "https://api.genetics.opentargets.org/graphql"
    
    def __init__(self, **data):
        super().__init__(**data)
        self._session = requests.Session()
        self._session.headers.update({
            'Content-Type': 'application/json'
        })

    def query_variant(self, variant_id: str) -> Dict[str, Any]:
        """Query information about a specific variant."""
        query = """
        query variantInfo($variantId: String!) {
            variant(variantId: $variantId) {
                id
                rsId
                chromosome
                position
                refAllele
                altAllele
                qtls {
                    typeId
                    sourceId
                    aggregatedScore
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
        
        try:
            response = self._session.post(
                self.base_url,
                json={'query': query, 'variables': {'variantId': variant_id}}
            )
            response.raise_for_status()
            return {"result": response.json()}
        except Exception as e:
            return {"error": f"Failed to query variant {variant_id}: {str(e)}"}

    def query_gene(self, gene_symbol: str) -> Dict[str, Any]:
        """Query genetic associations for a gene."""
        query = """
        query geneInfo($geneSymbol: String!) {
            genes(queryString: $geneSymbol) {
                id
                symbol
                chromosome
                start
                end
                bioType
                description
            }
        }
        """
        
        try:
            response = self._session.post(
                self.base_url,
                json={'query': query, 'variables': {'geneSymbol': gene_symbol}}
            )
            response.raise_for_status()
            return {"result": response.json()}
        except Exception as e:
            return {"error": f"Failed to query gene {gene_symbol}: {str(e)}"}

    def use(self, input_text: str) -> Dict[str, Any]:
        """Main interface that handles both variant and gene queries."""
        query = input_text.strip()
        
        if query.lower().startswith('rs'):
            return self.query_variant(query)
        else:
            return self.query_gene(query)

def get_variant_to_QTLs_opentarget(variant_id: str) -> Dict[str, Any]:
    """Deprecated: Use OpenTargetsGeneticsAPI class instead."""
    tool = OpenTargetsGeneticsAPI()
    return tool.query_variant(variant_id)

def otg_graphql(query: str) -> Dict[str, Any]:
    """Deprecated: Use OpenTargetsGeneticsAPI class instead."""
    tool = OpenTargetsGeneticsAPI()
    return tool.use(query)

if __name__ == '__main__':
    tool = OpenTargetsGeneticsAPI()
    
    # Test variant query
    variant_result = tool.use("rs58991260")
    print("Variant query result:", variant_result)
    
    # Test gene query
    gene_result = tool.use("BRCA1")
    print("Gene query result:", gene_result)