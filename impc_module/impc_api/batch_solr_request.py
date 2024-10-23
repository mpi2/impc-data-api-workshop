import json
import warnings
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm
from IPython.display import display

from impc_api.utils.validators import DownloadFormatValidator
from impc_api.utils.warnings import (
    warning_config,
    RowsParamIgnored,
    UnsupportedDownloadFormatError,
)
from .solr_request import solr_request

# Initialise warning config
warning_config()

def batch_solr_request(
    core, params, download=False, batch_size=5000, filename="batch_request"
):
    """Function for large API requests (>1,000,000 results). Fetches the data in batches and
    produces a Pandas DataFrame or downloads a file in json or csv formats.

    Additionally, allows to search multiple items in a list provided they belong to them same field.

    Args:
        core (str): name of IMPC solr core.
        params (dict): dictionary containing the API call parameters.
        download (bool, optional): True for download a local file, False to display results as a DataFrame. Defaults to False.
        batch_size (int, optional): Size of batches to fetch the data. Defaults to 5000.
        filename (str, optional): When download=True, select the name of the file. Defaults to 'batch_request'.


    Returns:
        pd.DataFrame: if download=False, displays a DataFrame with the results.
        None: if download=True, displays a statement on the console and returns None.
    """

    # If params["rows"] is passed, the user is warned about no effect
    if params.get("rows") is not None:
        warnings.warn(
            message='The "rows" param will be ignored in batch_solr_request. To set a batch size, specify a "batch_size" argument.',
            category=RowsParamIgnored,
        )

    # Set params for batch request
    params["start"] = 0  # Start at the first result
    # Override param rows in case there was input. Defines batch size to 5000 by default
    params["rows"] = batch_size

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

    # # Download only logic
    # If user decides to download, a generator is used to fetch data in batches without storing results in memory.
    if download:
        try:
            # Check if the format is supported
            DownloadFormatValidator(wt=params["wt"])

            # Implement loop behaviour
            print("Downloading file...")
            filename_path = Path(f"{filename}.{params['wt']}")
            gen = _batch_solr_generator(core, params, num_results)
            _solr_downloader(params, filename_path, gen)
            print(f"File saved as: {filename_path}")
        except UnsupportedDownloadFormatError as e:
            raise e
        except Exception as e:
            raise (f"An error ocurred while downloading the data:{e}")

            # Try to read the downloaded file
        try:
            print("Reading downloaded file...")
            return _read_downloaded_file(filename_path, params["wt"])
        except Exception as e:
            raise Exception(f"An unexpected error occured:{e}")

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
            case "y" | "":
                print("Fetching data...")
                return _batch_to_df(core, params, num_results)


# Helper batch_to_df
def _batch_to_df(core, params, num_results):
    """Helper function to fetch data in batches and display them in a DataFrame

    Args:
        core (str): name of IMPC solr core.
        params (dict): dictionary containing the API call parameters.
        num_results (int): Number of docs available

    Returns:
        pd.DataFrame: DataFrame with the results.
    """
    start = params["start"]
    batch_size = params["rows"]
    chunks = []
    # If the 'wt' param was changed by error, we set it to 'json'
    params["wt"] = "json"

    # Request chunks until we have complete data.
    with tqdm(total=num_results) as pbar:
        while start < num_results:
            # Request chunk. We don't need num_results anymore because it does not change.
            _, df_chunk = solr_request(
                core=core,
                params={**params, "start": start, "rows": batch_size},
                silent=True,
            )

            # Update progress bar with the number of rows requested.
            pbar.update(batch_size)
            pbar.refresh()
            # Record chunk.
            chunks.append(df_chunk)
            # Increment start.
            start += batch_size
        # Prepare final dataframe.
        return pd.concat(chunks, ignore_index=True)


def _batch_solr_generator(core, params, num_results):
    """Generator function to fetch results from the SOLR API in batches using pagination.

    Args:
        core (str): name of IMPC solr core.
        params (dict): dictionary containing the API call parameters.
        num_results (int): Number of docs available

    Raises:
        Exception: If a problem occurs during the download, an exception is raised.

    Yields:
        ([dict, str]): A JSON object or plain text with the results.
    """
    base_url = "https://www.ebi.ac.uk/mi/impc/solr/"
    solr_url = base_url + core + "/select"
    start = params["start"]
    batch_size = params["rows"]

    with tqdm(total=num_results) as pbar:
        while start <= num_results:
            params["start"] = start
            response = requests.get(solr_url, params=params, timeout=10)

            if response.status_code == 200:
                if params.get("wt") == "json":
                    data = response.json()["response"]["docs"]
                else:
                    data = response.text

                # Update and refresh the progress bar after getting the data
                pbar.update(batch_size)
                pbar.refresh()
                yield data

            else:
                raise Exception(f"Request failed. Status code: {response.status_code}")

            # pbar.update(batch_size)
            start += batch_size
        print(f"Your request URL after the last call:{response.url}")


# File writer
def _solr_downloader(params, filename, solr_generator):
    """Function to write the data from the generator into the specified format.
    Supports json and csv only.

    Args:
        params (dict): dictionary containing the API call parameters.
        filename (Path): name for the file to be downloaded. Defaults to "core.format" as passed by parent function.
        solr_generator ([dict, str]): Generator object with the results.
    """
    with open(filename, "w", encoding="UTF-8") as f:
        if params.get("wt") == "json":
            f.write("[\n")
            first_chunk = True

            for chunk in solr_generator:
                for item in chunk:
                    if not first_chunk:
                        f.write(",\n")
                    json.dump(item, f, ensure_ascii=False)
                    first_chunk = False
            f.write("\n]\n")

        elif params.get("wt") == "csv":
            first_chunk = True
            for chunk in solr_generator:
                lines = chunk.splitlines()
                if first_chunk:
                    # Write all lines in the first chunk
                    f.write(chunk)
                    first_chunk = False
                else:
                    # Skip the first line (header) in subsequent chunks
                    f.write("\n" + "\n".join(lines[1:]) + "\n")


# File reader
def _read_downloaded_file(filename: Path, request_format):
    """Wrapper for reading files into Pandas DataFrames

    Args:
        filename (Path): Name of the file to read
        request_format (str): Format of the file to read. Only 'json' and 'csv' are supported.

    Raises:
        MemoryError: When there is not enough memory to read the file.

    Returns:
        pd.DataFrame: Returns a pd.DataFrame with the data from the file.
    """
    try:
        match request_format:
            case "json":
                return pd.read_json(filename)
            case "csv":
                return pd.read_csv(filename)
    except MemoryError as exc:
        raise MemoryError(
            "MemoryError: Insuficient memory to read the file. Consider reading file in batches using Pandas or Polars."
        ) from exc
