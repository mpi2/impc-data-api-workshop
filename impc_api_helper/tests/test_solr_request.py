import pytest
from unittest.mock import patch
from solr_request import solr_request
import io
from contextlib import redirect_stdout
from .test_helpers import check_url_and_params


class TestSolrRequest:
    """Test class for the Solr Request function

    Uses a mock response (fixture) to mimic the content returned after fetching the solr API.
    Each mock response is parameterized to have different response content and status code based on the API call.
    Each test uses a different version of the mock response and asserts that the function returns the correct values.
    """

    # Fixture containing the core for solr_request test
    @pytest.fixture
    def core(self):
        return "test_core"

    # Fixture containing the params of a normal solr_request
    @pytest.fixture
    def common_params(self):
        return {"q": "*:*", "rows": 4, "wt": "json"}

    # Create a response fixture with modifiable status code and response content
    @pytest.fixture
    def mock_response(self, request):
        """
        Fixture to mock the response from the Solr API.

        Args:
            request (FixtureRequest): Request object provided by pytest containing the parameterized data

        Yields:
            MagicMock: A mock object "representing" the requests.get function used in solr_request.py.
                        Its returned value is configured according to the parameterized data.
        """
        with patch("solr_request.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.status_code = request.param.get("status_code")
            mock_response.json.return_value = request.param.get("json")
            yield mock_get

    # Parameter containing a successful mock response
    @pytest.mark.parametrize(
        "mock_response",
        [
            {
                "status_code": 200,
                "json": {
                    "response": {
                        "numFound": 67619,
                        "start": 0,
                        "docs": [
                            {"id": 1978, "name": "Toto"},
                            {"id": 1979, "name": "Hydra"},
                        ],
                    }
                },
            }
        ],
        indirect=True,
    )

    # 200: Successful test
    def test_successful_request(sef, mock_response, core, common_params):
        """Tests a successful request to the Solr API

        Args:
            mock_response (MagicMock): A mock object "representing" the response from the Solr API
            The parameters passed above are its contents
        """

        # Call function
        num_found, df = solr_request(core=core, params=common_params)

        # Assert results
        assert num_found == 67619
        assert df.shape == (2, 2)
        assert df.iloc[0, 0] == 1978
        assert df.iloc[0, 1] == "Toto"
        assert df.iloc[1, 0] == 1979
        assert df.iloc[1, 1] == "Hydra"

        # Verify that the mock was called
        mock_response.assert_called_once()

        # Check the status code
        assert mock_response.return_value.status_code == 200

        # Check the URL and parameters
        # Checks the url and params called are as expected.
        check_url_and_params(
            mock_response, expected_core=core, expected_params=common_params
        )

    # Parameter containing expected 404 response
    @pytest.mark.parametrize(
        "mock_response", [{"status_code": 404, "json_data": {}}], indirect=True
    )
    # 404: Error test
    def test_solr_request_error(self, mock_response, core, common_params):
        """Tests an unsuccessful request to the Solr API with status_code 404.

        Args:
            mock_response (MagicMock): A mock object "representing" the response from the Solr API
            The parameters passed above are its contents
        """

        # Capture stdout
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            result = solr_request(core=core, params=common_params)

        # Assert results
        assert result is None  # Assuming your function returns None on error

        # Check if "Error" was printed to console
        assert "Error" in captured_output.getvalue()

        # Verify that the mock was called
        mock_response.assert_called_once()

        # Check the status code
        assert mock_response.return_value.status_code == 404

        # Check the URL and parameters
        # Checks the url and params called are as expected.
        check_url_and_params(
            mock_response, expected_core=core, expected_params=common_params
        )

    # Test for the facet request
    # Params for a facet request
    @pytest.fixture
    def facet_params(self):
        return {
            "q": "*:*",
            "rows": 0,
            "facet": "on",
            "facet.field": "colour",
            "facet.limit": 3,
            "facet.mincount": 1,
        }

    # Parameter containing a facet request response
    @pytest.mark.parametrize(
        "mock_response",
        [
            {
                "status_code": 200,
                "json": {
                    "response": {
                        "numFound": 1961,
                        "docs": [],
                    },
                    "facet_counts": {
                        "facet_queries": {},
                        "facet_fields": {
                            "colour": [
                                "red",
                                1954,
                                "blue",
                                1963,
                                "black",
                                1984,
                            ]
                        },
                    },
                },
            }
        ],
        indirect=True,
    )
    def test_successful_facet_request(self, mock_response, core, facet_params):
        # Call the function on facetmode
        num_found, df = solr_request(core=core, params=facet_params)

        # Assert results
        assert num_found == 1961
        assert df.shape == (3, 2)
        assert df.iloc[0, 0] == "red"
        assert df.iloc[0, 1] == 1954
        assert df.iloc[1, 0] == "blue"
        assert df.iloc[1, 1] == 1963
        assert df.iloc[2, 0] == "black"
        assert df.iloc[2, 1] == 1984

        # Verify that the mock was called
        mock_response.assert_called_once()

        # Check the status code
        assert mock_response.return_value.status_code == 200

        # Checks the url and params called are as expected.
        check_url_and_params(
            mock_response, expected_core=core, expected_params=facet_params
        )
