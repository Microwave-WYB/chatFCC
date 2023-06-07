from langchain.utilities import SerpAPIWrapper
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from config import *
import argparse
import os

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("criteria", help="What kind of companies are you looking for?")
    args = arg_parser.parse_args()

    serpapi_api_key = os.environ.get('SERPAPI_API_KEY') if not SERPAPI_API_KEY else SERPAPI_API_KEY
    llm = OpenAI(temperature=0)

    prompt_template = PromptTemplate(
        input_variables=["criteria"],
        template="Output a search query to search on Google for companies that satisfies the criteria: {criteria}."
    )

    chain = LLMChain(llm=llm, prompt=prompt_template)
    serpapi = SerpAPIWrapper(serpapi_api_key=serpapi_api_key)
    query = chain.run({"criteria": args.criteria})
    results = serpapi.run(query)

    prompt_template = PromptTemplate(
        input_variables=["criteria", "results"],
        template="Output a list of companies that satisfies the criteria: {criteria}.\n Based on the search results from Google: {results}.\n Each company should be on a new line. Enclose the company list with triple backticks (```). Be as comprehensive as possible."
    )
    chain = LLMChain(llm=llm, prompt=prompt_template)
    response = chain.run({"criteria": args.criteria, "results": results})
    lines = response.split("\n")
    # Get the lines between the triple backticks
    companies = lines[lines.index("```") + 1:lines.index("```", lines.index("```") + 1)]
    companies = "\n".join(companies)
    print(companies)