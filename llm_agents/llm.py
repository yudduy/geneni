# import openai
import os

from pydantic import BaseModel
from typing import List

# taken from https://ai.google.dev/gemini-api/docs/get-started/python
import pathlib
import textwrap

import google.generativeai as genai

from IPython.display import display
from IPython.display import Markdown

try:
    import vertexai
    from vertexai.preview.generative_models import GenerativeModel, Part
    from google.cloud.aiplatform_v1beta1.types import SafetySetting, HarmCategory
    PROJECT_ID = 1
    vertexai.init(project=PROJECT_ID, location="us-central1")
except Exception as e:
    print(e)
    print("Could not load VertexAI API.")

# Used to securely store your API key
# from google.colab import userdata



# modified from https://github.com/snap-stanford/MLAgentBench/blob/main/MLAgentBench/LLM.py#L117
class ChatLLM(BaseModel):
    model: str = 'GEMINI 1.5'
    temperature: float = 0.0
    # genai.api_key = os.environ["GOOGLE_API_KEY"]  # Credentials setup
    
    # Or use `os.getenv('GOOGLE_API_KEY')` to fetch an environment variable.
    GOOGLE_API_KEY: str = os.getenv('GOOGLE_GENAI_API_KEY')
    #genai.configure(api_key=GOOGLE_API_KEY)
    
    def to_markdown(text):
        text = text.replace('•', '  *')
        return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

    
#    def generate(self, prompt: str, stop: List[str] = None):    
#        model = genai.GenerativeModel('gemini-pro')
#        response = model.generate_content(prompt)
        
#        reptext = response.text
        #print("---------\n", response.text, "\n", "---------------")
        
#        return response.text
        # return        
        # self.to_markdown(reptext)
        
    #def complete_text_gemini(prompt, stop_sequences=[], model="gemini-pro", max_tokens_to_sample = 2000, temperature=0.5, log_file=None, **kwargs):
    def complete_text_gemini(self, prompt, stop_sequences=[], max_tokens_to_sample = 2000, temperature=0.5, log_file=None, **kwargs):
        """ Call the gemini API to complete a prompt."""
        # Load the model
        model = genai.GenerativeModel("gemini-pro")
        #model = GenerativeModel("gemini-pro")
        # Query the model
        parameters = {
                "temperature": temperature,
                "max_output_tokens": max_tokens_to_sample,
                "stop_sequences": stop_sequences,
                **kwargs
            }
        safety_settings = {
                harm_category: SafetySetting.HarmBlockThreshold(SafetySetting.HarmBlockThreshold.BLOCK_NONE)
                for harm_category in iter(HarmCategory)
            }
        safety_settings = {
            }
        response = model.generate_content( [prompt] , generation_config=parameters, safety_settings=safety_settings)
        #print(f"prompt: {prompt}\n")
        #print(f"[prompt]: {[prompt]}\n")        
        #response = model.generate_content([prompt])
        #print(response.text)
        completion = response.text
        if log_file is not None:
            log_to_file(log_file, prompt, completion, model, max_tokens_to_sample)
        return completion
        
# fix this line below, genai doesn't have "chat completion"
        
#         response = openai.ChatCompletion.create(
#             model=self.model,
#             messages=[{"role": "user", "content": prompt}],
#             temperature=self.temperature,
#             stop=stop
#         )
#        return response.choices[0].message.content

if __name__ == '__main__':
    llm = ChatLLM()
    result = llm.complete_text_gemini(prompt='Who is the president of the USA?')
    print(result)
