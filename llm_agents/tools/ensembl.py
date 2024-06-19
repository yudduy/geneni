import sys
import json
import time

# Python 2/3 adaptability
try:
    from urllib.parse import urlparse, urlencode
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    from urlparse import urlparse
    from urllib import urlencode
    from urllib2 import urlopen, Request, HTTPError

import requests
from llm_agents.tools.base import ToolInterface

class ensembl_rest_client(ToolInterface):
    
    name: str = "ensembl_rest_client"
    description: str = (
        "Use this to get gene information from the Ensembl API. It will return details about the gene based on the given gene symbol or ID. "
        "Input: a valid gene symbol or ID (e.g. BRCA1)"
    )
    server: str = 'http://rest.ensembl.org'
        
    reqs_per_sec: int = 15
    req_count: int = 0
    last_req: int = 0        
        
#     def __init__(self, server='http://rest.ensembl.org', reqs_per_sec=15):
#         self.server = server
#         self.reqs_per_sec = reqs_per_sec
#         self.req_count = 0
#         self.last_req = 0

    def perform_rest_action(self, endpoint, hdrs=None, params=None):
        if hdrs is None:
            hdrs = {}

        if 'Content-Type' not in hdrs:
            hdrs['Content-Type'] = 'application/json'

        if params:
            endpoint += '?' + urlencode(params)

        data = None

        # check if we need to rate limit ourselves
        if self.req_count >= self.reqs_per_sec:
            delta = time.time() - self.last_req
            if delta < 1:
                time.sleep(1 - delta)
            self.last_req = time.time()
            self.req_count = 0
        
        try:
            request = Request(self.server + endpoint, headers=hdrs)
            response = urlopen(request)
            content = response.read()
            if content:
                data = json.loads(content)
            self.req_count += 1

        except HTTPError as e:
            # check if we are being rate limited by the server
            if e.code == 429:
                if 'Retry-After' in e.headers:
                    retry = e.headers['Retry-After']
                    time.sleep(float(retry))
                    self.perform_rest_action(endpoint, hdrs, params)
            else:
                sys.stderr.write('Request failed for {0}: Status code: {1.code} Reason: {1.reason}\n'.format(endpoint, e))
           
        return data

    def get_variants(self, species, symbol):
        genes = self.perform_rest_action(
            endpoint='/xrefs/symbol/{0}/{1}'.format(species, symbol), 
            params={'object_type': 'gene'}
        )
        if genes:
            stable_id = genes[0]['id']
            variants = self.perform_rest_action(
                '/overlap/id/{0}'.format(stable_id),
                params={'feature': 'variation'}
            )
            return variants
        return None

    def use(self, input_text: str) -> dict:
        """Fetches and formats gene information from the Ensemble API."""
        
#         datalist = input_text.split(",", 1) 
#         print(datalist)

        species = 'human' 
        symbol = input_text.strip(); 
#         species, symbol = input_text.split(",", 1) 
#         species, symbol = species.strip(), symbol.strip()
        
        try:
            variants = self.get_variants(species, symbol)
            formatted_str = "Gene Information:\n"            
            if variants:
                for v in variants[:10]:
                    formatted_str += '{seq_region_name}:{start}-{end}:{strand} ==> {id} ({consequence_type})'.format(**v)
                return {"result": formatted_str}
            else:
                return {"result": "No information found for the given gene symbol or ID."}
        except Exception as e:
            return {"error": str(e)}
        
        
# def run(species, symbol):
#     client = ensembl_rest_client()
#     variants = client.get_variants(species, symbol)
#     if variants:
#         for v in variants:
#             print('{seq_region_name}:{start}-{end}:{strand} ==> {id} ({consequence_type})'.format(**v))

if __name__ == '__main__':
    if len(sys.argv) == 3:
        species, symbol = sys.argv[1:]
    else:
        species, symbol = 'human', 'BRAF'

    client = ensembl_rest_client()
    res = client.use(f"{species},{symbol}")
#     res = client.use("human,BRAF")

    print(res) 