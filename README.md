# Geneni: A LLM Agent for Biological Data Analysis and Drug Discovery

## Overview

**Geneni** is an AI Agent for biological data analysis and supports drug discovery. Built on the [llm_agents](https://github.com/mpaepper/llm_agents/tree/main) framework, it features enhanced tools, Gemini API integration, and optimized prompts for precise biological evaluations.

## Features

- **Biological Data Analysis**: Geneni interpret biological databases and attempts to retrieve relevant information for user's inquiry.
- **Drug Discovery Support**: We built Geneni to specifically optimize the drug discovery process.
- **Integrated Tools**: Geneni is equipped with a suite of credible tools. 
- **Gemini API Integration**: Geneni uses the Gemini API.
- **Prompt Engineering and Fine-Tuning**: We have carefully engineered prompts and fine-tuned the model to ensure Geneni's responses are highly relevant and accurate for biological contexts. If the AI agent cannot find a conclusive answer, it will recommend users to add in other necessary databases/tools as requested by the AI Agent.

## Live Demo

We have a live demo of **Geneni** available at [https://geneni.streamlit.app/](https://geneni.streamlit.app/). 

### How to Use the Demo
1. Visit the live demo page.
2. Provide your Google Cloud API key when prompted.
3. Interact with the agent to explore its capabilities.

Feel free to test the features and see how **Geneni** can assist you with biological data analysis and drug discovery!

## Getting Started

### Prerequisites

Ensure you have the following installed:
- Python 3.7 or higher
- pip
- Git
- **Gemini API Key**: You will need a valid Gemini API key to use the Gemini API features. 

### Installation

Clone the Geneni repository:
```bash
git clone https://github.com/yudduy/geneni.git
cd geneni
```

Install the required dependencies:
```bash
pip install -r requirements.txt
```

### Configuration

To use the Gemini API, set your API key as an environment variable. You can do this by adding the following line to your `.bashrc`, `.bash_profile`, or `.env` file:

```bash
export GEMINI_API_KEY='your_api_key_here'
```

## Contact

For any questions or inquiries, please contact us at [duynguy@stanford.edu](mailto:duynguy@stanford.edu).

## Acknowledgments

Special thanks to the original [llm_agents](https://github.com/mpaepper/llm_agents/tree/main) project for providing the foundation for Geneni.
