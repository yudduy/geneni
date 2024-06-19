import datetime
import re
import time
from pydantic import BaseModel
from typing import List, Dict, Tuple
from llm_agents.llm import ChatLLM
from llm_agents.tools.base import ToolInterface
from llm_agents.tools.otgquery import get_variant_to_QTLs_opentarget, otg_graphql
from llm_agents.tools.geneclintable import get_gene_clintable
from llm_agents.tools.ensembl import ensembl_rest_client
from llm_agents.tools.snpsclintable import get_snp_clintable
from llm_agents.tools.disgenet import DisGeNETClient
from llm_agents.tools.diseaseclintable import get_disease_clintable
from llm_agents.tools.genetodisease import GeneToDisease

FINAL_ANSWER_TOKEN = "Final Answer:"
OBSERVATION_TOKEN = "Observation:"
THOUGHT_TOKEN = "Thought:"
PROMPT_TEMPLATE = """You are a helpful biologist. You have access to the following tools:

{tool_description}

Research Problem: {question}
You do not know anything about this problem so far.

Follow these instructions and do not forget them:
- First, come up with a high level plan based on your understanding of the problem and available tools and record it in the Research Plan and Status. You can revise the plan later.
- Research Plan and Status should well organized and succinctly keep track of 1) high level plan (can be revised), 2) what steps have been done and what steps are in progress, 3) short results and conclusions of each step after it has been performed. Do not perform action in research plan.
- Research Plan and Status must only include progress that has been made by previous steps. It should not include results not directly confirmed by the previous observation.
- Follow the plan and try to achieve the goal as straightforwardly as possible. 
- Use tools as necessary but not needed to iterate over all the tools. You must use exactly one of the available tools in every action. Each tool may be used more than once. Use tools best fit for the following research problem. Use only relevant tools to get a definite answer.
- If GeneToDisease does not find an association/returns an empty list, then ignore the results, and use the other tools to come to a conclusion. 
- Here is the script you should always run to answer the questions. You will always be asked this question: "is rsID associated to this disease?". To answer this question, first, use tools related to SNP, like get_variant_to_QTLs_opentarget, to retrieve relevant genes. Then, inquire further about the associated genes and determine if it relates to the disease. 
- You can always use other tools to inquire more. Avoid using tools that are not related to the current tasks. Only use additional tools when a tool returns an error. 
- When inputting a disease to observation, ensure that the input text is original. That means that you are not concatenating two words with a +. Keep them original as the user's prompt unless they misspelled it. 
- Highlight the supporting experiment results and reasoning before drawing any conclusions.
- Be very rigorous, critical, and skeptical of the result. Acknowledge the limitation. We want to avoid false positive discovery. Nonetheless, avoid making general, inconclusive statement like "it is uncertain and hard to draw conclusion". Your goal is to find a definite answer. 
- Do not try installing any new packages or libraries.
- If you believe you have solved the problem, you can use the Final Answer action to submit your answer. You can only submit once, so double check that you have achieved the goal before submitting. With each answer you give. Briefly elaborate on why they are true or false. 
- Once you found that a gene is associated with a disease. Conclude that statement into the final answer and do not run anything else.
- In the case of not having enough evidence, mention specifically what sort of information is needed to make an appropriate conclusion and how users can go about attaining it. 

Always respond in this format exactly:

Reflection: What does the observation mean? If there is an error, what caused the error and how to debug?
Critique: What assumption is this reflection making? How will this reasoning be wrong?
Research Plan and Status: The full high level research plan, with current status and confirmed results of each step briefly annotated. It must only include progress that has been made by previous steps. If there is any update, signify which section had an update by prefexing with double asterisks **like this. If there is no update, just copy the previous step Research Plan and Status. The high level plan from the previous step should be fully retained, unless it is intentionally revised.
Thought: What you are currently doing, what actions to perform and why
Action: the action to take, only relevant elements of {tool_names}, DO NOT contain tool input as it should be included in Action Input
Action Input: the input to the action
Observation: the result of the action
Final Answer: your final answer to the original input question

Begin!

Reflection: {previous_responses}
"""

class Agent(BaseModel):
    llm: ChatLLM
    tools: List[ToolInterface]
    prompt_template: str = PROMPT_TEMPLATE
    max_loops: int = 15
    max_retries: int = 3  # Add a max_retries attribute for handling retries
    # The stop pattern is used, so the LLM does not hallucinate until the end
    stop_pattern: List[str] = [f'\n{OBSERVATION_TOKEN}', f'\n\t{OBSERVATION_TOKEN}']

    @property
    def tool_description(self) -> str:
        return "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])

    @property
    def tool_names(self) -> str:
        return ",".join([tool.name for tool in self.tools])

    @property
    def tool_by_names(self) -> Dict[str, ToolInterface]:
        return {tool.name: tool for tool in self.tools}

    def run(self, question: str):
        previous_responses = []
        num_loops = 0
        prompt = self.prompt_template.format(
                today=datetime.date.today(),
                tool_description=self.tool_description,
                tool_names=self.tool_names,
                question=question,
                previous_responses='{previous_responses}'
        )
        print(prompt.format(previous_responses=''))
        
        while num_loops < self.max_loops:
            num_loops += 1
            curr_prompt = prompt.format(previous_responses='\n'.join(previous_responses))
            generated, tool, tool_input = self.decide_next_action(curr_prompt)

            if tool == 'Final Answer':
                return tool_input

            retries = 0
            while retries < self.max_retries:
                try:
                    # Attempt to get the tool from the dictionary
                    if tool not in self.tool_by_names or tool is None:
                        raise ValueError(f"Unknown tool: {tool}")
                    # Use the tool and process the result
                    tool_instance = self.tool_by_names[tool]
                    tool_result = tool_instance.use(tool_input)
                    generated += f"\n{OBSERVATION_TOKEN} {tool_result}\n{THOUGHT_TOKEN}"
                    print(generated)
                    previous_responses.append(generated)
                    break  # Exit the retry loop on success
                except ValueError as e:
                    print(f"Error: {e}")
                    break
                except Exception as e:
                    retries += 1
                    wait_time = 2 ** retries  # Exponential backoff
                    print(f"Encountered exception: {e}. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)

    def decide_next_action(self, prompt: str) -> str:
        generated = self.llm.complete_text_gemini(prompt, self.stop_pattern)
        
        tool, tool_input = self._parse(generated)
        return generated, tool, tool_input

    def _parse(self, generated: str) -> Tuple[str, str]:
        if FINAL_ANSWER_TOKEN in generated:
            return "Final Answer", generated.split(FINAL_ANSWER_TOKEN)[-1].strip()
        
        regex = r"Action: [\[]?(.*?)[\]]?[\n]*Action Input:[\s]*(.*)"
        match = re.search(regex, generated, re.DOTALL)
        if not match:
            raise ValueError(f"Output of LLM is not parsable for next tool use: `{generated}`")
            
        tool = match.group(1).strip()
        tool_input = match.group(2).strip(" ").strip('"')
        
        # No longer encode the tool input
        return tool, tool_input


if __name__ == '__main__':
    agent = Agent(llm=ChatLLM(), tools=[gene2disease()])
    result = agent.run("What is 7 * 9 - 34 in Python?")

    print(f"Final answer is {result}")
