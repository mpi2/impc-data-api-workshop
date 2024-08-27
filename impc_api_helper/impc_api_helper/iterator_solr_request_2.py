from IPython.display import display
import json
import pandas as pd
import requests
from tqdm import tqdm
from solr_request import solr_request
import logging
from pathlib import Path

def batch_solr_request(core, params, download=False, batch_size=5000, path_to_download='./'):
    # Set params for batch request
    params["start"] = 0  # Start at the first result
    params["rows"] = batch_size  # Fetch results in chunks of 5000

    # If user did not specify format, defaults to json.
    if params.get("wt") is None:
        params["wt"] = "json"

    # Check if it's multiple request
    if params.get("field_list") is not None:
        # Extract entities_list and entity_type from params
        field_list = params.pop("field_list")
        field_type = params.pop("field_type")

        # Construct the filter query with grouped model IDs
        fq = "{}:({})".format(
            field_type, " OR ".join(["{}".format(id) for id in field_list])
        )
        # Show users the field and field values they passed to the function
        print("Queried field:", fq)
        # Set internal params the users should not change
        params["fq"] = fq

    # Determine the total number of rows. Note that we do not request any data (rows = 0).
    num_results, _ = solr_request(
        core=core, params={**params, "start": 0, "rows": 0, "wt": "json"}, silent=True
    )
    print(f"Number of found documents: {num_results}")

    # Download/display only logic
    # If user decides to download, a generator is used to fetch data in batches without storing results in memory.
    if download:
        # Implement loop behaviour
        filename = Path(path_to_download) / f"{core}.{params['wt']}"
        gen = _batch_solr_generator(core, params, num_results)
        _solr_downloader(params, filename, gen)
        print("Showing the first batch of results only. See downloaded file for the whole data.")
        match params["wt"]:
            case "json":
                return pd.read_json(filename, nrows=batch_size, lines=True)
            case "csv":
                return pd.read_csv(filename, nrows=batch_size)

    # If the number of results is small enough and download is off, it's okay to show as df
    if num_results < 1000000 and not download:
        return _batch_to_df(core, params, num_results)

    # If it's too big, warn the user and ask if they want to proceed.
    else:
        print(
            "Your request might exceed the available memory. We suggest setting 'download=True' and reading the file in batches"
        )
        prompt = input(
            "Do you wish to proceed anyway? press ('y' or enter to proceed) / type('n' or 'exit' to cancel)"
        )
        match prompt:
            case "n" | "exit":
                print("Exiting gracefully")
                exit()
            case "y" | '':
                print("Fetching data...")
                return _batch_to_df(core, params, num_results)




# Helper batch_to_df
def _batch_to_df(core, params, num_results):
    start = params["start"]
    batch_size = params["rows"]
    chunks = []
    # If the 'wt' param was changed by error, we set it to 'json'
    params["wt"] = "json"

    # Request chunks until we have complete data.
    with tqdm(total=num_results) as pbar:
        while start < num_results:
            # Update progress bar with the number of rows requested.
            pbar.update(batch_size)

            # Request chunk. We don't need num_results anymore because it does not change.
            _, df_chunk = solr_request(
                core=core,
                params={**params, "start": start, "rows": batch_size},
                silent=True,
            )

            # Record chunk.
            chunks.append(df_chunk)
            # Increment start.
            start += batch_size
        # Prepare final dataframe.
        return pd.concat(chunks, ignore_index=True)


def _batch_solr_generator(core, params, num_results):
    base_url = "https://www.ebi.ac.uk/mi/impc/solr/"
    solr_url = base_url + core + "/select"
    start = params["start"]
    batch_size = params["rows"]

    with tqdm(total=num_results) as pbar:
        while start < num_results:
            params["start"] = start
            response = requests.get(solr_url, params=params, timeout=10)

            if response.status_code == 200:
                if params.get("wt") == "json":
                    data = response.json()["response"]["docs"]
                else:
                    data = response.text
                yield data
            else:
                raise Exception(f"Request failed. Status code: {response.status_code}")

            pbar.update(batch_size)
            start += batch_size


# File writer
def _solr_downloader(params, filename, solr_generator):
    with open(filename, "w", encoding="UTF-8") as f:
        for chunk in solr_generator:
            if params.get("wt") == "json":
                for item in chunk:
                    json.dump(item, f)
                    f.write("\n")
            else:
                f.write(chunk)
