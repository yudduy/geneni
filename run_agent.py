import os
import sys
from llm_agents.tools.base import ToolInterface
# Add the directory containing opentargets_client.py and other tools to the Python path
from llm_agents import Agent, ChatLLM, get_variant_to_QTLs_opentarget, otg_graphql, get_gene_clintable, ensembl_rest_client, get_snp_clintable, GeneToDisease


if __name__ == '__main__':
    prompt = input("Enter a question / task for the agent: ")
    agent = Agent(
        llm=ChatLLM(),
        tools=[
            ensembl_rest_client(),
            get_gene_clintable(),
            get_variant_to_QTLs_opentarget(),
            GeneToDisease(), 
            # get_snp_clintable(),
        ])
    result = agent.run(prompt)
    print(f"Final answer: {result}")
    