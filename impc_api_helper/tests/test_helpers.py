def check_url_status_code_and_params(mock_response, expected_status_code, expected_core, expected_params):
    """
    Check if the mocked response was called with the correct URL, core, and parameters.

    Args:
        mock_response: The mocked response object.
        expected_core (str): The expected Solr core in the URL.
        expected_params (dict): The expected query parameters.

    Raises:
        AssertionError: If any of the checks fail.
    """
    call_args = mock_response.call_args
    url = call_args[0][0]
    actual_params = call_args[1]["params"]

    # Verify that the mock was called
    mock_response.assert_called_once()

    # Check expected status code
    assert mock_response.return_value.status_code == expected_status_code

    # Check URL
    assert url.startswith("https://www.ebi.ac.uk/mi/impc/solr/"), "Incorrect base URL"
    assert expected_core in url, f"Expected core '{expected_core}' not found in URL"
    assert "select" in url, "'select' operation not found in URL"

    # Check parameters
    assert actual_params == expected_params, "Mismatch in query parameters"

    

    
