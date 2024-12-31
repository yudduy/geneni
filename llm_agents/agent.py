"""
This module implements the Agent class which orchestrates the interaction between
the LLM and various biological database tools. The agent interprets user queries,
selects appropriate tools, and generates comprehensive responses.

Key components:
- Tool management and selection
- Query processing and response generation
- Error handling and recovery mechanisms
- Support for both database queries and general knowledge questions
"""

import datetime
import re
import time
import json
from pydantic import BaseModel
from typing import List, Dict, Tuple, Optional, Callable
from llm_agents.llm import ChatLLM
from llm_agents.tools.toolinterface import ToolInterface

# Import all tool classes
from llm_agents.tools.opentargetgenetics import get_variant_to_QTLs_opentarget, otg_graphql
from llm_agents.tools.clinicaltable_gene import get_gene_clintable
from llm_agents.tools.ensembl import EnsemblTool
from llm_agents.tools.clinicaltable_snp import get_snp_clintable
from llm_agents.tools.disgenet import DisGeNETClient
from llm_agents.tools.clinicaltable_disease import get_disease_clintable
from llm_agents.tools.genetodisease import GeneToDisease

# Define tokens for response parsing
FINAL_ANSWER_TOKEN = "Final Answer:"
OBSERVATION_TOKEN = "Observation:"
THOUGHT_TOKEN = "Thought:"

# Update prompt template to be more explicit about biological queries
PROMPT_TEMPLATE = """You are a helpful biologist with expertise in genetics and disease associations. You have access to the following tools:

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

IMPORTANT: You must ALWAYS respond in this EXACT format:

Reflection: [Your reflection here]
Critique: [Your critique here]
Research Plan and Status: [Your research plan here]
Thought: [Your current thought process]
Action: [ONE tool name from the available tools]
Action Input: [The input for the selected tool]

If you have a final answer:
Final Answer: [Your final answer here]

For general knowledge questions that don't require database lookups, you can provide a Final Answer directly.

Begin!

Reflection: {previous_responses}
"""

class Agent(BaseModel):
    """Manages the interaction between LLM and biological database tools.
    
    Attributes:
        llm (ChatLLM): Language model instance
        tools (List[ToolInterface]): Available database tools
        prompt_template (str): Template for generating prompts
        max_loops (int): Maximum iterations for tool usage
        max_retries (int): Maximum retries for failed attempts
        thought_callback (Optional[Callable[[str], None]]): Callback for logging thoughts
    """
    
    llm: ChatLLM
    tools: List[ToolInterface]
    prompt_template: str = PROMPT_TEMPLATE
    max_loops: int = 10
    max_retries: int = 3
    stop_pattern: List[str] = [f'\n{OBSERVATION_TOKEN}', f'\n\t{OBSERVATION_TOKEN}']
    thought_callback: Optional[Callable[[str], None]] = None

    @property
    def tool_description(self) -> str:
        """Generate description of available tools."""
        return "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])

    @property
    def tool_names(self) -> str:
        """Get comma-separated list of tool names."""
        return ",".join([tool.name for tool in self.tools])

    @property
    def tool_by_names(self) -> Dict[str, ToolInterface]:
        """Create mapping of tool names to tool instances."""
        return {tool.name: tool for tool in self.tools}

    def determine_query_type(self, question: str) -> str:
        """Determine if the query needs biological database access."""
        prompt = f"""Analyze this query: "{question}"

Please classify this query as either:
1. GENERAL - A general conversation or basic question
2. BIO - A biological/medical/genetic query that might need database verification

RESPONSE_TYPE: [GENERAL/BIO]
CONFIDENCE: [HIGH/MEDIUM/LOW]
REASON: [Brief explanation]"""

        response = self.llm.complete_text_gemini(prompt)
        
        if "RESPONSE_TYPE: GENERAL" in response:
            return "GENERAL"
        return "BIO"

    def handle_general_query(self, question: str) -> str:
        """Handle general conversation without database access."""
        prompt = f"""You are a helpful and friendly AI assistant. Please respond to: {question}

Keep your response natural and conversational. If you detect the conversation might benefit 
from biological database information, suggest that to the user."""

        return self.llm.complete_text_gemini(prompt)

    def _log_thought(self, thought: str):
        """Log a thought, both to console and callback if available."""
        if self.thought_callback:
            self.thought_callback(thought)

    def run(self, question: str):
        """Process queries using context-aware approach."""
        try:
            query_type = self.determine_query_type(question)
            self._log_thought(f"Query type: {query_type}")
            
            if query_type == "GENERAL":
                response = self.handle_general_query(question)
                self._log_thought("Providing conversational response")
                return response
            
            initial_response = self._get_initial_response(question)
            if not self._needs_verification(initial_response):
                return self._extract_answer(initial_response)

            self._log_thought("Preparing to verify with databases")
            user_input = input().strip().lower()
            
            if user_input != 'yes':
                return self._extract_answer(initial_response)

            return self._run_database_verification(question)
            
        except Exception as e:
            return f"An error occurred: {str(e)}"

    def _get_initial_response(self, question: str) -> str:
        """Get the initial response from the LLM."""
        prompt = f"""As a biology expert, please answer this question: {question}

Provide:
1. A clear, scientific answer
2. Confidence level (HIGH/MEDIUM/LOW)
3. Whether database verification would be helpful

Format:
ANSWER: [Your explanation]
CONFIDENCE: [HIGH/MEDIUM/LOW]
NEEDS_VERIFICATION: [YES/NO]
REASON: [Why verification might be needed]"""

        return self.llm.complete_text_gemini(prompt)

    def _needs_verification(self, initial_response: str) -> bool:
        """Determine if verification is needed."""
        return "NEEDS_VERIFICATION: YES" in initial_response

    def _extract_answer(self, initial_response: str) -> str:
        """Extract the answer from the initial response."""
        return initial_response.split("ANSWER:")[1].split("CONFIDENCE:")[0].strip()

    def _run_database_verification(self, question: str) -> str:
        """Run database verification."""
        # This method is not implemented in the original code, so it's left unchanged.
        # You may want to implement this method based on your specific requirements.
        pass


if __name__ == '__main__':
    agent = Agent(llm=ChatLLM(), tools=[gene2disease()])
    result = agent.run("What is 7 * 9 - 34 in Python?")

    print(f"Final answer is {result}")
