from iterator_solr_request_2 import batch_solr_request
import pandas as pd

markers = ['"Cthrc1"', '*11']
df = batch_solr_request(
    core="genotype-phenotype",
    params={
        "q": "*:*",
        "fl": "marker_symbol,mp_term_name,p_value",
        'field_list': markers,
        'field_type': 'marker_symbol'
    },
    download=True,
)

df = pd.read_json('genotype-phenotype.json', nrows=80000, lines=True)
# df = pd.read_csv('genotype-phenotype.csv', nrows=80000)
# df = pd.read_xml('genotype-phenotype.xml', parser='etree')
print(df.shape)
