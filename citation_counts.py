import requests
from bs4 import BeautifulSoup
import pandas as pd

def get_citation_count(tool_name):
    search_url = f"https://scholar.google.com/scholar?hl=en&q={tool_name}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    result_stats = soup.find('div', {'id': 'gs_ab_md'})

    if result_stats:
        text = result_stats.get_text()
        # Extract the number of results from the text
        if 'About' in text:
            count_str = text.split('About ')[1].split(' ')[0].replace(',', '')
        else:
            count_str = text.split(' ')[1].replace(',', '')
        return int(count_str)
    return 0

tools = ["CP2K", "Quantum Espresso", "VASP(Vienna Ab initio Simulation Package)", "ABINIT", "NWChem"]

citation_counts = {tool: get_citation_count(tool) for tool in tools}

citation_counts_df = pd.DataFrame(list(citation_counts.items()), columns=["Tool", "Citations"])
citation_counts_df = citation_counts_df.sort_values(by="Citations", ascending=False)

print(citation_counts_df)

citation_counts_df.to_csv('citation_counts.csv', index=False)

