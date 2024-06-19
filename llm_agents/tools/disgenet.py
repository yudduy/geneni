import sys
import time
import requests
from urllib.parse import urlencode
from pydantic import BaseModel, Field
from llm_agents.tools.base import ToolInterface

class DisGeNETClient(ToolInterface):
    api_host: str = 'https://www.disgenet.org/api'
    reqs_per_sec: int = 15
    req_count: int = 0
    last_req: float = 0
    api_key: str = Field(None, exclude=True)
    session: requests.Session = Field(default_factory=requests.Session, exclude=True)

    def __init__(self, email, password):
        super().__init__(name="disgenet_client", description=(
            "Use this to get variant-disease associations from the DisGeNET API. "
            "It will return details about the diseases associated with a given variant."
        ))  # Initialize ToolInterface with required fields
        self.api_key = self.authenticate(email, password)
        self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def authenticate(self, email, password):
        auth_params = {"email": email, "password": password}
        url = f"{self.api_host}/auth/"
        response = requests.post(url, data=auth_params)
        if response.status_code == 200:
            return response.json().get("token")
        else:
            raise Exception(f"Authentication failed: {response.status_code} {response.text}")

    def perform_rest_action(self, endpoint, params=None):
        if params:
            endpoint += '?' + urlencode(params)
        
        if self.req_count >= self.reqs_per_sec:
            delta = time.time() - self.last_req
            if delta < 1:
                time.sleep(1 - delta)
            self.last_req = time.time()
            self.req_count = 0

        try:
            response = self.session.get(self.api_host + endpoint)
            if response.status_code == 200:
                self.req_count += 1
                return response.json()
            elif response.status_code == 429:
                retry = int(response.headers.get('Retry-After', 1))
                time.sleep(retry)
                return self.perform_rest_action(endpoint, params)
            else:
                response.raise_for_status()
        except requests.exceptions.RequestException as e:
            sys.stderr.write(f"Request failed for {endpoint}: {e}\n")
            return None

    def get_variant_disease_associations(self, variant_id):
        return self.perform_rest_action(f"/vda/variants/{variant_id}")

    def use(self, input_text: str) -> dict:
        variant_id = input_text.strip()
        try:
            associations = self.get_variant_disease_associations(variant_id)
            if associations:
                formatted_str = "Variant-Disease Associations:\n"
                for assoc in associations:
                    formatted_str += (
                        f"Variant: {assoc['variant']}\n"
                        f"Disease: {assoc['disease_name']} ({assoc['disease_id']})\n"
                        f"Score: {assoc['score']}\n\n"
                    )
                return {"result": formatted_str}
            else:
                return {"result": "No associations found for the given variant ID."}
        except Exception as e:
            return {"error": str(e)}

    class Config:
        arbitrary_types_allowed = True

if __name__ == '__main__':
    email = "duynguy@stanford.edu"
    password = "d0604000d8e8f4a419f2895b51061a11f7cb7278"
    variant_id = "rs295"  # Example variant ID

    client = DisGeNETClient(email, password)
    res = client.use(variant_id)
    print(res)

