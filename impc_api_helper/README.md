# IMPC_API_HELPER
README for draft `impc_api_helper` python package.

The functions in this package are intended for use on a Jupyter Notebook.

## Installing the package for the first time
1. Clone the repository and navigate into it. Navigate into the package name until you can see `setup.py` and `pyproject.toml`
2. Run `python3 -m build`, this builds the package, a couple of new files/folders will appear.
3. Install the package running `pip install .`
4. Try it out: Go to Jupyter Notebook and some examples below:

### Available functions
The available functions can be imported as:

```
from impc_api_helper import solr_request, batch_solr_request
```

### Solr request
The most basic request to the IMPC solr API
```
num_found, df = solr_request( core='genotype-phenotype', params={
        'q': '*:*',
        'rows': 10, 
        'fl': 'marker_symbol,allele_symbol,parameter_stable_id'
    }
)
```

#### Solr request validation
A common pitfall when writing a query is the misspelling of `core` and `fields` arguments. For this, we have included an `validate` argument that raises a warning when these values are not as expected. Note this does not prevent you from executing a query; it just alerts you to a potential issue.

##### Core validation
```
num_found, df = solr_request( core='invalid_core', params={
        'q': '*:*',
        'rows': 10
    },
    validate=True
)

> InvalidCoreWarning: Invalid core: "genotype-phenotyp", select from the available cores:
> dict_keys(['experiment', 'genotype-phenotype', 'impc_images', 'phenodigm', 'statistical-result']))
```

##### Field list validation
```
num_found, df = solr_request( core='genotype-phenotype', params={
        'q': '*:*',
        'rows': 10,
        'fl': 'invalid_field,marker_symbol,allele_symbol'
    },
    validate=True
)
> InvalidFieldWarning: Unexpected field name: "invalid_field". Check the spelling of fields.
> To see expected fields check the documentation at: https://www.ebi.ac.uk/mi/impc/solrdoc/
```

#### Facet request
`solr_request` allows facet requests

```
num_found, df = solr_request(
     core="genotype-phenotype",
     params={
         "q": "*:*",
         "rows": 0,
         "facet": "on",
         "facet.field": "zygosity",
         "facet.limit": 15,
         "facet.mincount": 1,
     },
 )
```

### Batch Solr Request
`batch_solr_request` is available for large queries. This solves issues where a request is too large to fit into memory or where it puts a lot of strain on the API. 

Use `batch_solr_request` for:
- Large queries (>1,000,000)
- Querying multiple items in a list
- Downloading data in `json` or `csv` format.

#### Large queries
For large queries you can choose between seeing them in a DataFrame or downloading them in `json` or `csv` format.

##### Large query - see in DataFrame
This will fetch your data using the API responsibly and return a Pandas DataFrame

When your request is larger than recommended and you have not opted for downloading the data, a warning will be presented and you should follow the instructions to proceed.

```
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

##### Large query - Download
When using the `download=True` option, no DataFrame will be returned, instead a file with the requested information will be saved to the path specified in `path_to_download`. 

```
batch_solr_request(
    core='genotype-phenotype',
    params={
        'q':'*:*',
        'wt':'csv'
    },
    download=True,
    path_to_download = '.',
    batch_size=20000
)
```

#### Query by multiple values
`batch_solr_request` also allows to search multiple items in a list provided they belong to them same field.
Pass the list to the `field_list` param and specify the type of `fl` in `field_type`.

```
# List of gene symbols
genes = ["Zfp580","Firrm","Gpld1","Mbip"]

df = batch_solr_request(
    core='genotype-phenotype',
    params={
        'q':'*:*',
        'fl': 'marker_symbol,mp_term_name,p_value',
        'field_list': genes,
        'field_type': 'marker_symbol'
    },
    download = False
print(df.head())
)
```
This too can be downloaded

```
# List of gene symbols
genes = ["Zfp580","Firrm","Gpld1","Mbip"]

batch_solr_request(
    core='genotype-phenotype',
    params={
        'q':'*:*',
        'fl': 'marker_symbol,mp_term_name,p_value',
        'field_list': genes,
        'field_type': 'marker_symbol'
    },
    download = True,
    path_to_download='downloads'
)
```



