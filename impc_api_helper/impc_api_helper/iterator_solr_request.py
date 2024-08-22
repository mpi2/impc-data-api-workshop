import csv
import json

import requests


# Helper function to fetch results. This function is used by the 'iterator_solr_request' function.
def entity_iterator(base_url, params):
    """Generator function to fetch results from the SOLR server in chunks using pagination

    Args:
        base_url (str): The base URL of the Solr server to fetch documents from.
        params (dict): A dictionary of parameters to include in the GET request. Must include
                       'start' and 'rows' keys, which represent the index of the first document
                       to fetch and the number of documents to fetch per request, respectively.

    Yields:
        dict: The next document in the response from the Solr server.
    """
    # Initialise variable to check the first request
    first_request = True

    # Call the API in chunks and yield the documents in each chunk
    while True:
        response = requests.get(base_url, params=params)
        data = response.json()
        docs = data["response"]["docs"]

        # Print the first request only
        if first_request:
            print(f"Your first request: {response.url}")
            first_request = False

        # Yield the documents in the current chunk
        for doc in docs:
            yield doc

        # Check if there are more results to fetch
        start = params["start"] + params["rows"]
        num_found = data["response"]["numFound"]
        if start >= num_found:
            break

        # Update the start parameter for the next request
        params["start"] = start

    # Print last request and total number of documents retrieved
    print(f"Your last request: {response.url}")
    print(f'Number of found documents: {data["response"]["numFound"]}\n')


# Function to iterate over field list and write results to a file.
def iterator_solr_request(
    core, params, filename="iteration_solr_request", format="json"
):
    """Function to fetch results in batches from the Solr API and write them to a file.
    Defaults to fetching 5000 rows at a time.
    Avoids cluttering local memory, ideal for large requests.
    
    Args:
        core (str): The name of the Solr core to fetch results from.
        params (dict): A dictionary of parameters to use in the filter query. Must include
                       'field_list' and 'field_type' keys, which represent the list of field items (i.e., list of MGI model identifiers)
                        to fetch and the type of the field (i.e., model_id) to filter on, respectively.
        filename (str): The name of the file/path to write the results to. Defaults to 'iteration_solr_request'.
        format (str): The format of the output file. Can be 'csv' or 'json'. Defaults to 'json'.

    Returns: None

    Example use case:
        # List of model IDs.
        models = ['MGI:3587188', 'MGI:3587185', 'MGI:3605874', 'MGI:2668213']

        # Call iterator function
        iterator_solr_request(
            core='phenodigm',
            params = {
                'q': 'type:disease_model_summary',
                'fl': 'model_id,marker_id,disease_id',
                'field_list': models,
                'field_type': 'model_id'
            },
            filename='model_ids',
            format='csv'
        )
    """

    # Validate format
    if format not in ["json", "csv"]:
        raise ValueError("Invalid format. Please use 'json' or 'csv'")

    # Base URL
    base_url = "https://www.ebi.ac.uk/mi/impc/solr/"
    solr_url = base_url + core + "/select"

    # Extract entities_list and entity_type from params
    field_list = params.pop("field_list")
    field_type = params.pop("field_type")

    # Construct the filter query with grouped model IDs
    fq = "{}:({})".format(
        field_type, " OR ".join(['"{}"'.format(id) for id in field_list])
    )

    # Show users the field and field values they passed to the function
    print("Queried field:", fq)
    # Set internal params the users should not change
    params["fq"] = fq
    params["wt"] = "json"
    params["start"] = 0  # Start at the first result
    params["rows"] = 5000  # Fetch results in chunks of 5000

    try:
        # Fetch results using a generator function
        results_generator = entity_iterator(solr_url, params)
    except Exception as e:
        raise Exception("An error occurred while downloading the data: " + str(e))

    # Append extension to the filename
    filename = f"{filename}.{format}"

    try:
        # Open the file in write mode
        with open(filename, "w", newline="") as f:
            if format == "csv":
                writer = None
                for item in results_generator:
                    # Initialize the CSV writer with the keys of the first item as the field names
                    if writer is None:
                        writer = csv.DictWriter(f, fieldnames=item.keys())
                        writer.writeheader()
                    # Write the item to the CSV file
                    writer.writerow(item)
                    # Write to json without loading to memory.
            elif format == "json":
                f.write("[")
                for i, item in enumerate(results_generator):
                    if i != 0:
                        f.write(",")
                    json.dump(item, f)
                f.write("]")
    except Exception as e:
        raise Exception("An error occurred while writing the file: " + str(e))

    print(f"File {filename} was created.")
