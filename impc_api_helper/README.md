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

`from impc_api_helper import solr_request, batch_request, iterator_solr_request`

### Solr request
The most basic request to the IMPC solr API
```
num_found, df = solr_request( core='genotype-phenotype', params={
        'q': '*:*'
        'rows': 10
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

### Batch request
For larger requests, use the batch request function to query the API responsibly.
```
df = batch_request(
    core="genotype-phenotype",
    params={
        'q': 'top_level_mp_term_name:"cardiovascular system phenotype" AND effect_size:[* TO *] AND life_stage_name:"Late adult"',
        'fl': 'allele_accession_id,life_stage_name,marker_symbol,mp_term_name,p_value,parameter_name,parameter_stable_id,phenotyping_center,statistical_method,top_level_mp_term_name,effect_size'
    },
    batch_size=100
)
```

### Iterator solr request
To pass a list of different fields and download a file with the information
```
# Genes example
genes = ["Zfp580","Firrm","Gpld1","Mbip"]

# Initial query parameters
params = {
    'q': "*:*",
    'fl': 'marker_symbol,allele_symbol,parameter_stable_id',
    'field_list': genes,
    'field_type': "marker_symbol"
}
iterator_solr_request(core='genotype-phenotype', params=params, filename='marker_symbol', format ='csv')
```
