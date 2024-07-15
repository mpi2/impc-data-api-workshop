from IPython.display import display
from tqdm import tqdm
from urllib.parse import unquote

import pandas as pd
import requests

# Display the whole dataframe <15
pd.set_option("display.max_rows", 15)
pd.set_option("display.max_columns", None)


def facet_request(core, params, silent=False):
    """Performs a single Solr request to retrieve faceted search results.

    Provides a summary of data distribution across the specified fields.

    Example query:
        num_found, df = facet_request(
        core='genotype-phenotype',
        params={
            'q': '*:*',
            'rows': 0,
            'facet': 'on',
            'facet.field': 'zygosity',
            'facet.limit': 15,
            'facet.mincount': 1
        }
    )

    Args:
        core (str): name of IMPC solr core
        params (dict): dictionary containing the API call parameters
        silent (bool, optional): When True, displays: URL of API call, the number of found docs and a portion of the DataFrame. Defaults to False.

    Returns:
        num_found: Number of docs found.
        pandas.DataFrame: Pandas.DataFrame object with the information requested.

    """

    base_url = "https://www.ebi.ac.uk/mi/impc/solr/"
    solr_url = base_url + core + "/select"

    response = requests.get(solr_url, params=params)
    if not silent:
        print(f"\nYour request:\n{unquote(response.request.url)}\n")

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        num_found = data["response"]["numFound"]
        if not silent:
            print(f"Number of found documents: {num_found}\n")
        # Extract and add faceting query results to the list
        facet_counts = data["facet_counts"]["facet_fields"][params["facet.field"]]
        # Initialize an empty dictionary
        faceting_dict = {}
        # Iterate over the list, taking pairs of elements
        for i in range(0, len(facet_counts), 2):
            # Assign label as key and count as value
            label = facet_counts[i]
            count = facet_counts[i + 1]
            faceting_dict[label] = [count]

        # Print the resulting dictionary
        # Convert the list of dictionaries into a DataFrame and print the DataFrame
        df = pd.DataFrame(faceting_dict)
        df = pd.DataFrame.from_dict(
            faceting_dict, orient="index", columns=["counts"]
        ).reset_index()

        # Rename the columns
        df.columns = [params["facet.field"], "count_per_category"]
        if not silent:
            display(df)
        return num_found, df

    else:
        print("Error:", response.status_code, response.text)
