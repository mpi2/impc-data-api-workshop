import pytest
from unittest.mock import patch
from solr_request import solr_request
import io
from contextlib import redirect_stdout
from .test_helpers import check_url_and_params


class TestSolrRequest:
    # Create a response fixture with modifiable status code and response content
    @pytest.fixture
    def mock_response(self, request):
        with patch("solr_request.requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.status_code = request.param.get("status_code")
            mock_response.json.return_value = request.param.get("json")
            yield mock_get

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
    # Sucessful test
    def test_successful_request(self, mock_response):
        # Call function
        num_found, df = solr_request(
            core="test_core", params={"q": "*:*", "rows": 4, "wt": "json"}
        )

        # Assert results
        assert num_found == 67619
        assert df.shape == (2, 2)
        assert df.iloc[0, 0] == 1978
        assert df.iloc[0, 1] == "Toto"
        assert df.iloc[1, 0] == 1979
        assert df.iloc[1, 1] == "Hydra"

        # Verify that the mock was called
        mock_response.assert_called_once()

        check_url_and_params(mock_response)

    # 404 test
    @pytest.mark.parametrize(
        "mock_response", [{"status_code": 404, "json_data": {}}], indirect=True
    )
    def test_solr_request_error(self, mock_response):
        # Capture stdout
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            result = solr_request(
                core="test_core", params={"q": "*:*", "rows": 4, "wt": "json"}
            )

        # Assert results
        assert result is None  # Assuming your function returns None on error

        # Check if "Error" was printed to console
        assert "Error" in captured_output.getvalue()

        # Verify that the mock was called
        mock_response.assert_called_once()

        # Check the status code
        assert mock_response.return_value.status_code == 404

        # Check the URL and parameters (if still relevant for error case)
        check_url_and_params(mock_response)
