import requests
from llm_agents.tools.base import ToolInterface
from pprint import pprint

class get_snp_clintable(ToolInterface):
    name: str = "get_snp_clintable"
    description: str = (
        "Use this to get SNP information from the Clinical Tables API. It will return details about the SNP based on the given rsNum. "
        "Input: a valid rsNum (e.g. rs12345)"
    )
    url: str = 'https://clinicaltables.nlm.nih.gov/api/snps/v3/search'

    def execute_query(self, term: str, max_list: int = 10) -> dict:
        """Executes a query to the Clinical Tables API and returns the data as a dictionary."""
        params = {
            'terms': term,
            'maxList': max_list
        }
        response = requests.get(self.url, params=params)
        response.raise_for_status()  # Raise an error for bad response codes
        return response.json()

    def format_snp_info_output(self, data):
        if not data[3]:
            return "No information found for the given rsNum."

        formatted_data = []
        for item in data[3]:
            snp_info = {
                "rsNum": item[0],
                "38.chr": item[1],
                "38.pos": item[2],
                "38.alleles": item[3],
                "38.gene": item[4]
            }
            formatted_data.append(snp_info)

        return formatted_data

    def use(self, input_text: str) -> dict:
        """Fetches and formats SNP information from the Clinical Tables API."""
        rsNum = input_text.strip()
        try:
            data = self.execute_query(rsNum)
            output = self.format_snp_info_output(data)
            return {"result": output}
        except requests.RequestException as e:
            return {"error": f"Request failed: {e}"}
        except Exception as e:
            return {"error": str(e)}

if __name__ == '__main__':
    s = get_snp_clintable()
    res = s.use("rs12345")
    pprint(res)