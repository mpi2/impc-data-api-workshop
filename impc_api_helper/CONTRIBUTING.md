# CONTRIBUTING.MD

## Dependencies:
The package is build using [setuptools](https://setuptools.pypa.io/en/latest/userguide/quickstart.html) and [build](https://build.pypa.io/en/stable/installation.html).
1. `pip install build` -- This installs setuptools automatically. 

## Installing the package for the first time
1. Clone the repository and navigate into it. Navigate into the package name until you can see `setup.py` and `pyproject.toml`
2. Run `python3 -m build`, this builds the package, a couple of new files/folders will appear.
3. Install the package running `pip install .`
4. Try it out: Go to Jupyter Notebook and try:


```
from impc_api_helper import solr_request
num_found, df = solr_request( core='genotype-phenotype', params={
        'q': '*:*'
        'rows': 10
        'fl': 'marker_symbol,allele_symbol,parameter_stable_id'
    }
)
```

## Making changes after installation 

- Make the changes to the `.py` modules, if there are any **dependency** changes, change them in both `pyproject.toml` and `setup.py`
- To clean previous builds, re-build and reinstall run these 3 commands:
```
# Step 1: Clean previous builds
rm -rf build dist *.egg-info

# Step 2: Build the package
python -m build

# Step 3: Reinstall the updated package
pip install . --force-reinstall

```
- Your changes should have effect upon reloading the import of the package. 


