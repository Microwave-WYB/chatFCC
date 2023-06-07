from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.chains.question_answering import load_qa_chain
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.document_loaders import PyPDFLoader
from langchain.vectorstores import Chroma
from pypdf import PdfReader
import argparse

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a pdf file.
    """
    pdf = PdfReader(pdf_path)
    text = ''
    for page in pdf.pages:
        text += page.extract_text()
    return text

def analyze_large_manual(path: str, chain_type: str = "stuff"):
    """
    Analyze a large manual using the LLM model given the path to the manual.
    """
    assert chain_type in ["stuff", "map_reduce", "map_rerank", "refine"]
    loader = PyPDFLoader(path)
    docs = loader.load()
    embeddings = OpenAIEmbeddings()
    docsearch = Chroma.from_documents(docs, embeddings).as_retriever()

    queries = []
    queries.append("Describe the product in one sentence\n")
    queries.append("Potential use cases of the product\n")
    queries.append("Mac address or prefix of the product if any\n")
    queries.append("SSID/Name of the product if any.\n")
    queries.append("Default username / password / pin if any\n")
    responses = []
    llm = OpenAI(temperature=0)
    chain = load_qa_chain(llm=llm, chain_type=chain_type)
    for query in queries:
        relavant_docs = docsearch.get_relevant_documents(query)
        response = chain({"input_documents":relavant_docs, "question":query}, return_only_outputs=True)["output_text"]
        responses.append(response)
    with open(path.replace(".pdf", f"_{chain_type}.txt"), "w") as f:
        for i, response in enumerate(responses):
            f.write(f"{i+1}. {response}\n")
        print(f"Saved to {path.replace('.pdf', f'_{chain_type}.txt')}")

def analyze_manual(path: str):
    """
    Analyze a manual using the LLM model given the path to the manual.
    """
    text = extract_text_from_pdf(path)
    template = "Given a manual to a wireless product, answer in the following format:\n"
    template += "1. Describe the product in one sentence\n"
    template += "2. Potential use cases of the product\n"
    template += "3. Mac address or prefix of the product if any\n"
    template += "4. SSID/Name of the product if any.\n"
    template += "5. Default username / password / pin if any\n"
    template += "Manual:\n{text}"
    prompt = PromptTemplate(
        input_variables=["text"],
        template=template,
    )
    llm = OpenAI(temperature=0)
    chain = LLMChain(llm=llm, prompt=prompt)
    response = chain.run(text)
    with open(path.replace(".pdf", ".txt"), "w") as f:
        f.write(response)
    print(response)

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("path", help="Path to the pdf file")
    arg_parser.add_argument("--chain_type", help="Type of chain to use, one of stuff, map_reduce, map_rerank, refine", default="stuff")
    args = arg_parser.parse_args()
    path = args.path
    chain_type = args.chain_type
    analyze_large_manual(path, chain_type)