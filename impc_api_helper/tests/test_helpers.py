  # Helper function with assertions for each test
def check_url_and_params(mock_response):
    call_args = mock_response.call_args
    url = call_args[0][0]
    params = call_args[1]["params"]

    assert url.startswith("https://www.ebi.ac.uk/mi/impc/solr/")
    assert "test_core" in url
    assert "select" in url
    assert params == {"q": "*:*", "rows": 4, "wt": "json"}