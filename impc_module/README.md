# IMPC_API

`impc_api` is a Python package.
  
The functions in this package are intended for use in a Jupyter Notebook.

## Installation Instructions

1. **Create a virtual environment (optional but recommended)**:
On Mac:
 ```bash
 python3 -m venv .venv
 source .venv/bin/activate
 ```

2. **Install the package**: `pip install impc_api`
3. **Install Jupyter**: `pip install jupyter`
4. **Run the Jupyter Notebook**: `jupyter notebook`

After executing the command, the Jupyter interface should open in your browser. If it does not, follow the instructions provided in the terminal.

5. **Try it out**:

Create a [Jupyter Notebook](https://jupyter-notebook.readthedocs.io/en/latest/) and try some of the examples below:

## Available functions

The available functions can be imported as:

```python
from impc_api import solr_request, batch_solr_request
```

# 1. Solr request

The most basic request to the IMPC solr API

```python
num_found, df = solr_request(
    core='genotype-phenotype', 
    params={
        'q': '*:*',
        'rows': 10, 
        'fl': 'marker_symbol,allele_symbol,parameter_stable_id'
    }
)
```

## a. Facet request

`solr_request` allows facet requests

```python
num_found, df = solr_request(
    core="genotype-phenotype",
    params={
         "q": "*:*",
         "rows": 0,
         "facet": "on",
         "facet.field": "zygosity",
         "facet.limit": 15,
         "facet.mincount": 1,
    }
)
```

## b. Solr request validation

A common pitfall when writing a query is the misspelling of `core` and `fields` arguments. For this, we have included a `validate` argument that raises a warning when these values are not as expected. Note this does not prevent you from executing a query; it just alerts you to a potential issue.

### Core validation

```python
num_found, df = solr_request(
    core='invalid_core',
    params={
        'q': '*:*',
        'rows': 10
    },
    validate=True
)

> InvalidCoreWarning: Invalid core: "genotype-phenotyp", select from the available cores:
> dict_keys(['experiment', 'genotype-phenotype', 'impc_images', 'phenodigm', 'statistical-result'])
```

### Field list validation

```python
num_found, df = solr_request(
    core='genotype-phenotype',
    params={
        'q': '*:*',
        'rows': 10,
        'fl': 'invalid_field,marker_symbol,allele_symbol'
    },
    validate=True
)
> InvalidFieldWarning: Unexpected field name: "invalid_field". Check the spelling of fields.
> To see expected fields check the documentation at: https://www.ebi.ac.uk/mi/impc/solrdoc/
```

# 2. Batch Solr Request

`batch_solr_request` is available for large queries. This solves issues where a request is too large to fit into memory or where it puts a lot of strain on the API.

Use `batch_solr_request` for:

- Large queries (>1,000,000)
- Querying multiple items in a list
- Downloading data in `json` or `csv` format.

## Large queries

For large queries you can choose between seeing them in a DataFrame or downloading them in `json` or `csv` format.

## a. Large query - see in DataFrame

This will fetch your data using the API responsibly and return a Pandas DataFrame

When your request is larger than recommended and you have not opted for downloading the data, a warning will be presented and you should follow the instructions to proceed.

```python
df = batch_solr_request(
    core='genotype-phenotype',
    params={
        'q':'*:*'
    },
    download=False,
    batch_size=30000
)
print(df.head())
```

## b. Large query - Download

When using the `download=True` option, a file with the requested information will be saved as `filename`. The format is selected based on the `wt` parameter.
A DataFrame may be returned, provided it does not exceed the memory available on your laptop. If the DataFrame is too large, an error will be raised. For these cases, we recommend you read the downloaded file in batches/chunks.  

```python
df = batch_solr_request(
    core='genotype-phenotype',
    params={
        'q':'*:*',
        'wt':'csv'
    },
    download=True,
    filename='geno_pheno_query',
    batch_size=100000
)
print(df.head())
```

## c. Query by multiple values

`batch_solr_request` also allows to search multiple items in a list provided they belong to them same field.
Pass the list to the `field_list` param and specify the type of `fl` in `field_type`.

```python
# List of gene symbols
genes = ["Zfp580", "Firrm", "Gpld1", "Mbip"]

df = batch_solr_request(
    core='genotype-phenotype',
    params={
        'q':'*:*',
        'fl': 'marker_symbol,mp_term_name,p_value',
        'field_list': genes,
        'field_type': 'marker_symbol'
    },
    download = False
)
print(df.head())
```

This can be downloaded too:

```python
# List of gene symbols
genes = ["Zfp580", "Firrm", "Gpld1", "Mbip"]

df = batch_solr_request(
    core='genotype-phenotype',
    params={
        'q':'*:*',
        'fl': 'marker_symbol,mp_term_name,p_value',
        'field_list': genes,
        'field_type': 'marker_symbol'
    },
    download = True,
    filename='gene_list_query'
)
print(df.head())
```
