import requests
from llm_agents.tools.base import ToolInterface
from pprint import pprint

class get_disease_clintable(ToolInterface):
    name: str = "get_disease_clintable"
    description: str = (
        "Use this to get disease information from the Clinical Tables API. It will return details about the disease based on the given term. "
        "Input: a valid disease term (e.g. cancer)"
    )
    url: str = 'https://clinicaltables.nlm.nih.gov/api/disease_names/v3/search'

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

    def format_disease_info_output(self, data):
        formatted_data = []

        if not data[1]:
            return "No information found for the given disease term."

        for idx, item in enumerate(data[1]):
            disease_info = {
                "Name": item,
                "Details": data[3][idx] if data[3] else None
            }
            formatted_data.append(disease_info)

        return formatted_data

    def use(self, input_text: str) -> dict:
        """Fetches and formats disease information from the Clinical Tables API."""
        term = input_text.strip().strip("```")
        try:
            data = self.execute_query(term)
            output = self.format_disease_info_output(data)
            return {"result": output}
        except Exception as e:
            return {"error": str(e)}

if __name__ == '__main__':
    s = get_disease_clintable()
    res = s.use("cystic fibrosis")
    pprint(res)

