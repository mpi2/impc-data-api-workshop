import json
from pathlib import Path
from unittest.mock import patch, call, Mock

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from impc_api.batch_solr_request import (
    batch_solr_request,
    _batch_solr_generator,
    solr_request,
    _batch_to_df,
    _solr_downloader,
    _read_downloaded_file,
)
from impc_api.utils.warnings import (
    RowsParamIgnored,
    UnsupportedDownloadFormatError,
)

# When rows is passed to batch solr request, a warning is raised.
# Let's ignore this warning in all tests except the one that asserts the warning
pytestmark = pytest.mark.filterwarnings(
    "ignore::impc_api.utils.warnings.RowsParamIgnored"
)


# Fixture containing the core
@pytest.fixture
def core():
    return "test_core"


# Fixture to create a temporary file for use in tests
@pytest.fixture(scope="function")
def temp_file_fixture(
    tmp_path,
):
    temp_dir = tmp_path / "temp_dir"
    temp_dir.mkdir(exist_ok=True)
    return temp_dir / "test_file"


class TestBatchSolrRequest:
    # Fixture containing the params of a normal batch_solr_request
    @pytest.fixture
    def common_params(self):
        return {"start": 0, "rows": 0, "wt": "json"}

    # Fixture mocking solr_request within the batch_solr_request module.
    # solr_request will be mocked with different values for numFound, therefore it is passed as param
    @pytest.fixture
    def mock_solr_request(self, request):
        with patch("impc_api.batch_solr_request.solr_request") as mock:
            # Mock expected return content of the solr_request (numFound and df)
            mock.return_value = (request.param, pd.DataFrame())
            yield mock

    # Fixture mocking _batch_to_df
    @pytest.fixture
    def mock_batch_to_df(self):
        with patch("impc_api.batch_solr_request._batch_to_df") as mock:
            # Mock expected return content of the _batch_to_df (pd.DataFrame)
            mock.return_value = pd.DataFrame()
            yield mock

    # Test no download - small request
    # Parameters to determine the numFound of mock_solr_request
    @pytest.mark.parametrize("mock_solr_request", [10000], indirect=True)
    def test_batch_solr_request_no_download_small_request(
        self, mock_solr_request, core, common_params, capsys, mock_batch_to_df
    ):
        # Call tested function
        result = batch_solr_request(
            core, params=common_params, download=False, batch_size=100
        )

        # Assert the value of params was changed to batch_size
        assert common_params["rows"] == 100

        # Assert the mock was called with the expected parameters (start = 0, rows = 0) despite calling other values.
        mock_solr_request.assert_called_with(
            core=core,
            params={**common_params, "start": 0, "rows": 0, "wt": "json"},
            silent=True,
        )

        # Retrieve the numFound
        num_found = mock_solr_request.return_value[0]
        # Capture stoud
        captured = capsys.readouterr()
        assert captured.out == f"Number of found documents: {num_found}\n"

        # Check _batch_to_df was called
        mock_batch_to_df.assert_called_once()

    # Test no download - large request
    # Set mock_solr_request to return a large numFound
    @pytest.mark.parametrize("mock_solr_request", [1000001], indirect=True)
    # Parameter to test 4 cases: when user selects 'y','' or 'n','exit' upon large download warning.
    @pytest.mark.parametrize(
        "user_input,expected_outcome",
        [("y", "continue"), ("", "continue"), ("n", "exit"), ("exit", "exit")],
    )
    def test_batch_solr_request_download_false_large_request(
        self,
        core,
        common_params,
        capsys,
        monkeypatch,
        mock_batch_to_df,
        mock_solr_request,
        user_input,
        expected_outcome,
    ):
        # Monkeypatch the input() function with parametrized user input
        monkeypatch.setattr("builtins.input", lambda _: user_input)

        # Set a batch_size for clarity
        batch_size = 500000

        # When user types 'n' or 'exit', exit should be triggered.
        if expected_outcome == "exit":
            with pytest.raises(SystemExit):
                batch_solr_request(
                    core, params=common_params, download=False, batch_size=batch_size
                )
        else:
            result = batch_solr_request(
                core, params=common_params, download=False, batch_size=batch_size
            )

        # Capture the exit messages
        captured = capsys.readouterr()

        # Retrieve numFound
        num_found = mock_solr_request.return_value[0]

        # Assertions for continue case
        assert f"Number of found documents: {num_found}" in captured.out

        if expected_outcome == "continue":
            assert (
                "Your request might exceed the available memory. We suggest setting 'download=True' and reading the file in batches"
                in captured.out
            )
            mock_batch_to_df.assert_called_with(
                "test_core", {"start": 0, "rows": batch_size, "wt": "json"}, num_found
            )

        # Assertion for exit case
        elif expected_outcome == "exit":
            assert "Exiting gracefully" in captured.out
            mock_batch_to_df.assert_not_called()

    # Test download - large request
    # Fixture mocking _batch_solr_generator
    @pytest.fixture
    def mock_batch_solr_generator(self):
        with patch("impc_api.batch_solr_request._batch_solr_generator") as mock:
            yield mock

    # Fixture mocking _solr_downloader. Yields a tmp_path to write a file for the duration of the test.
    @pytest.fixture
    def mock_solr_downloader(self, tmp_path):
        with patch("impc_api.batch_solr_request._solr_downloader") as mock:
            temp_dir = Path(tmp_path) / "temp_dir"
            temp_dir.mkdir()
            yield mock

    # Mock response for test containing 2,000,000 docs
    @pytest.mark.parametrize("mock_solr_request", [2000000], indirect=True)
    # Parametrized decorator to simulate reading a json and csv files
    @pytest.mark.parametrize(
        "params_format, format, file_content",
        [
            (
                {"start": 0, "rows": 0, "wt": "json"},
                "json",
                '[{"id": "1", "city": "Houston"},{"id": "2", "city": "Prague"}]',
            ),
            (
                {"start": 0, "rows": 0, "wt": "csv"},
                "csv",
                "id,city\n1,Houston\n2,Prague\n",
            ),
        ],
    )
    # This test should check the correct helper functions and print statements are called.
    # Calling the API and writing the file are tested within the helpers.
    def test_batch_solr_request_download_true(
        self,
        core,
        capsys,
        mock_solr_request,
        mock_batch_solr_generator,
        mock_solr_downloader,
        params_format,
        format,
        file_content,
        temp_file_fixture,
    ):
        # Write the file with corresponding content
        file_and_format = f"{temp_file_fixture}.{format}"
        Path(file_and_format).write_text(file_content)

        # First we call the function
        # We patch solr_request to get the number of docs
        result = batch_solr_request(
            core,
            params=params_format,
            download=True,
            filename=temp_file_fixture,
            batch_size=2000000,
        )
        num_found = mock_solr_request.return_value[0]

        # Assert params["rows"] == batch size and not the original value (0)
        assert params_format["rows"] == 2000000

        # Check _batch_solr_generator gets called once with correct args
        mock_batch_solr_generator.assert_called_once_with(
            core, params_format, num_found
        )

        # Check _solr_downloader gets called once with correct args
        # Checks the filename is a Path and has the corresponding format
        mock_solr_downloader.assert_called_once_with(
            params_format, Path(file_and_format), mock_batch_solr_generator.return_value
        )

        # Check the print statements
        captured = capsys.readouterr()
        assert f"Number of found documents: {num_found}" in captured.out
        assert f"File saved as: {file_and_format}" in captured.out

        # Check the function returns a df with expected content
        # Assert the structure of the final df
        assert_frame_equal(
            result,
            pd.DataFrame(
                {
                    "id": [1, 2],
                    "city": ["Houston", "Prague"],
                }
            ).reset_index(drop=True),
        )

    # Test the download validates parameters
    # Mock response for test containing 2,000,000 docs
    @pytest.mark.parametrize("mock_solr_request", [2000000], indirect=True)
    def test_batch_solr_request_download_true_validate_params_wt(
        self, core, mock_solr_request
    ):
        # Set a filename for the test
        filename = f"{core}"
        params = {"start": 0, "rows": 0, "wt": "wrong_format"}

        # Assert exception when the format is unsupported
        if format != "json" and format != "csv":
            with pytest.raises(UnsupportedDownloadFormatError):
                batch_solr_request(
                    core,
                    params=params,
                    download=True,
                    filename=filename,
                    batch_size=2000000,
                )

    # Test download - multiple fields - large and small
    # Mock params for a multiple field query
    @pytest.fixture
    def multiple_field_params(self):
        return {
            "q": "*:*",
            "rows": 0,
            "start": 0,
            "field_list": ['"orange"', "apple", "*berry"],
            "field_type": "fruits",
            "wt": "json",
        }

    # Mock response for test containing a large request and a small request
    @pytest.mark.parametrize("mock_solr_request", [(2000000), (10000)], indirect=True)
    @pytest.mark.parametrize(
        "download_bool",
        [(True), (False)],
    )
    def test_batch_solr_request_multiple_fields(
        self,
        core,
        multiple_field_params,
        capsys,
        mock_solr_request,
        mock_batch_solr_generator,
        download_bool,
        monkeypatch,
        mock_batch_to_df,
        mock_solr_downloader,
        temp_file_fixture,
    ):
        # This test should ensure the request is formatted properly. Regardless of going to downloads or to _batch_to_df
        # Retrieve  num_found
        num_found = mock_solr_request.return_value[0]
        # When download=False and numFound is > 1,000,001 we pass 'y' in this test case.
        if not download_bool and num_found == 2000000:
            monkeypatch.setattr("builtins.input", lambda _: "y")

        # Call test function
        # If download==True, create a temporary file and call with the path_to_download
        if download_bool:
            # Write the file with corresponding content
            file_content = '[{"id": "1", "city": "Cape Town"}]\n'
            file_and_format = f"{temp_file_fixture}.json"
            Path(file_and_format).write_text(file_content)

            result = batch_solr_request(
                core,
                params=multiple_field_params,
                download=download_bool,
                filename=temp_file_fixture,
            )
        else:
            # Otherwise, call without the path_to_download
            result = batch_solr_request(
                core,
                params=multiple_field_params,
                download=download_bool,
                batch_size=5000,
            )

        # Check output which should be equal for both.
        captured = capsys.readouterr()
        assert f"Number of found documents: {num_found}" in captured.out
        assert 'Queried field: fruits:("orange" OR apple OR *berry)' in captured.out

        # If download==True, check subsequent functions were executed
        if download_bool:
            # Check _batch_solr_generator gets called with correct args
            mock_batch_solr_generator.assert_called_with(
                core, multiple_field_params, num_found
            )

            # Check _solr_downloader gets called once with correct args
            mock_solr_downloader.assert_called_once_with(
                multiple_field_params,
                Path(file_and_format),
                mock_batch_solr_generator.return_value,
            )

            # Check the function returns a df with expected content
            # Assert the structure of the final df
            assert_frame_equal(
                result,
                pd.DataFrame(
                    {
                        "id": [1],
                        "city": ["Cape Town"],
                    }
                ).reset_index(drop=True),
            )

        # Otherwise, use the 'y' input at the start of the test and make sure the required function is executed.
        if not download_bool and num_found == 2000000:
            assert (
                "Your request might exceed the available memory. We suggest setting 'download=True' and reading the file in batches"
                in captured.out
            )
            # Check _batch_to_df was called with correct params
            mock_batch_to_df.assert_called_once_with(
                core, multiple_field_params, num_found
            )

            # Check the function returns a dataframe
            assert result is not None
            assert isinstance(result, pd.DataFrame) is True

    # Test the warning when params["rows"] is passed
    @pytest.mark.filterwarnings(
        "default::impc_api.utils.warnings.RowsParamIgnored"
    )
    @pytest.mark.parametrize("mock_solr_request", [10000], indirect=True)
    def test_param_rows_warning(core, common_params, mock_solr_request):
        with pytest.warns(RowsParamIgnored):
            batch_solr_request(core, params=common_params)


# Have helper functions in a different class to separate fixtures and parameters
class TestHelpersSolrBatchRequest:
    # Define a generator to produce df's dynamically
    def data_generator(self):
        """Generator to produce data dynamically (row by row or doc by doc)/

        Yields:
            Tuple: tuple containing an id number and a value
        """
        # Values for the dataframes
        animals = ["Bull", "Elephant", "Rhino", "Monkey", "Snake"]
        # Yield a tuple containing an id number and an animal string
        for i, a in enumerate(animals):
            yield (i, a)

    # Fixture mocking solr_request in the batch_solr_request module
    # Num_found is passed dynamically as params during the test
    # Generates df's dynamically using the data generator
    @pytest.fixture
    def mock_solr_request_generator(self, request):
        """Patches solr_request for _batch_to_df _batch_solr_generator producing a df dynamically.
        Creates a df in chunks (row by row) mocking incoming batches of responses.
        """
        with patch("impc_api.batch_solr_request.solr_request") as mock:
            # Call the generator
            data_generator = self.data_generator()

            # Use the side_effects to return num_found and the dfs
            def side_effect(*args, **kwargs):
                # Get the tuple from the data generator
                idx, animal = next(data_generator)
                # Create a df
                df = pd.DataFrame({"id": [idx], "animal": [animal]})
                return request.param, df

            mock.side_effect = side_effect
            yield mock

    # Fixture containing the params of a normal batch_solr_request with flexible number of rows (batch_size).
    @pytest.fixture
    def batch_params(self, batch_size):
        return {"start": 0, "rows": batch_size, "wt": "json"}

    # Fixture to pass different num_found values per test
    @pytest.fixture
    def num_found(self, request):
        return request.param

    # Parameters to be passsed to the test: a num_found value for mock_solr_request_generator, a num_found separately, and rows (batch_size).
    # Note num_found is returned by solr_request, when we access it using the generator function, it causes issues.
    # Hence, we pass num_found separately as a fixture.
    @pytest.mark.parametrize(
        "mock_solr_request_generator,num_found,batch_size",
        [(50000, 50000, 10000), (5, 5, 1), (25000, 25000, 5000)],
        indirect=["mock_solr_request_generator"],
    )
    def test_batch_to_df(
        self, core, batch_params, num_found, mock_solr_request_generator, batch_size
    ):
        # Call the tested function
        df = _batch_to_df(core, batch_params, num_found)

        # Assert solr_request was called with the expected params and increasing start
        expected_calls = [
            call(
                core=core,
                params={**batch_params, "start": i * batch_size, "rows": batch_size},
                silent=True,
            )
            for i in range(5)
        ]
        mock_solr_request_generator.assert_has_calls(expected_calls)

        # Assert the structure of the final df
        assert_frame_equal(
            df,
            pd.DataFrame(
                {
                    "id": [0, 1, 2, 3, 4],
                    "animal": ["Bull", "Elephant", "Rhino", "Monkey", "Snake"],
                }
            ).reset_index(drop=True),
        )

    # Test _batch_solr_generator
    # Fixture to mock the requests module
    @pytest.fixture
    def mock_requests_get(self, request):
        with patch("impc_api.batch_solr_request.requests.get") as mock_get:
            # Capture the format of the response
            wt = request.param["wt"]
            mock_get.return_value.format = wt

            # Get the status code and
            mock_get.return_value.status_code = request.param["status_code"]

            # Call the generator
            data_generator = self.data_generator()

            # Use the side_effects to return num_found and the response data
            def side_effect(*args, **kwargs):
                # Create a mock response object
                mock_response = Mock()
                mock_response.status_code = 200

                # Get the tuple from the data generator
                _, animal = next(data_generator)

                # Create type of response
                # if json
                if wt == "json":
                    mock_response.json.return_value = {
                        "response": {"docs": [{"id": animal}]}
                    }
                # if csv
                if wt == "csv":
                    mock_response.text = f"id,\n{animal}"

                return mock_response

            # Assign the side effect
            mock_get.side_effect = side_effect

            yield mock_get

    # Fixture containing the params for batch_solr_generator
    @pytest.fixture
    def batch_solr_generator_params(self):
        return {"q": "*:*", "start": 0, "rows": 1}

    # Parameters with the params for fixtures and the expected results
    @pytest.mark.parametrize(
        "mock_requests_get,expected_results",
        [
            (
                {"wt": "json", "status_code": 200},
                [
                    [{"id": "Bull"}],
                    [{"id": "Elephant"}],
                    [{"id": "Rhino"}],
                    [{"id": "Monkey"}],
                    [{"id": "Snake"}],
                ],
            ),
            (
                {"wt": "csv", "status_code": 200},
                [
                    "id,\nBull",
                    "id,\nElephant",
                    "id,\nRhino",
                    "id,\nMonkey",
                    "id,\nSnake",
                ],
            ),
        ],
        indirect=["mock_requests_get"],
    )
    def test_batch_solr_generator(
        self, core, batch_solr_generator_params, mock_requests_get, expected_results
    ):
        # Define num_found
        num_results = 5
        # Define the wt and batch_size param for the test
        batch_solr_generator_params["wt"] = mock_requests_get.return_value.format
        batch_size = 1

        # Override rows as the parent function would
        batch_solr_generator_params["rows"] = batch_size

        # Call the generator
        result = _batch_solr_generator(core, batch_solr_generator_params, num_results)

        # Loop over the expected results and check corresponding calls
        for idx, exp_result in enumerate(expected_results, start=0):
            # Call the next iteration
            assert next(result) == exp_result

            # Check requests.get was called with the correct url, params [especially, the 'start' param], and timeout.
            # The first call will always be with the params["rows"] value, 1 in this case.
            # Since the function
            mock_requests_get.assert_called_with(
                "https://www.ebi.ac.uk/mi/impc/solr/test_core/select",
                params={
                    **batch_solr_generator_params,
                    "start": idx,
                    "rows": batch_size,
                },
                timeout=10,
            )

    # Simpler approach to test when status code is not 200
    # Fixture to mock requests.get returning a status code.
    @pytest.fixture
    def mock_requests_get_error(self, request):
        with patch("impc_api.batch_solr_request.requests.get") as mock_get:
            mock_get.return_value.status_code = request.param
            yield mock_get

    # Params for _batch_solr_generator when status code is not 200
    @pytest.mark.parametrize(
        "mock_requests_get_error", [404, 500], indirect=["mock_requests_get_error"]
    )
    def test_batch_solr_generator_error(
        self, core, batch_solr_generator_params, mock_requests_get_error
    ):
        # Get status code:
        status_code = mock_requests_get_error.return_value.status_code
        # Call the generator and expect an exception to be raised
        # Note the num_found is passed but the number itself does not matter
        # Note list() is needed so that the generator is iterated otherwise exception is never reached.
        with pytest.raises(
            Exception, match=f"Request failed. Status code: {status_code}"
        ):
            _ = list(
                _batch_solr_generator(
                    core=core, params=batch_solr_generator_params, num_results=4
                )
            )

    # Fixture to mock _solr_generator.
    @pytest.fixture
    def mock_solr_generator(self, request):
        """
        Mocks a generator yielding 2 batches/chunks to the tested function
        """
        format = request.param
        if format == "json":

            def data_chunks():
                chunk_1 = [
                    {"id": idx, "number": number}
                    for idx, number in enumerate(range(0, 3))
                ]
                chunk_2 = [
                    {"id": idx, "number": number}
                    for idx, number in enumerate(range(100, 97, -1), start=3)
                ]

                yield chunk_1
                yield chunk_2

            yield data_chunks()
        elif format == "csv":

            def data_chunks():
                chunk_1 = "id,number\n" + "\n".join(
                    f"{idx},{number}" for idx, number in enumerate(range(0, 3))
                )
                chunk_2 = "id,number\n" + "\n".join(
                    f"{idx},{number}"
                    for idx, number in enumerate(range(100, 97, -1), start=3)
                )

                yield chunk_1
                yield chunk_2

            yield data_chunks()

    # Parameters for test function, one for the fixture and one as the expected format
    @pytest.mark.parametrize(
        "mock_solr_generator, expected_format",
        [("json", "json"), ("csv", "csv")],
        indirect=["mock_solr_generator"],
    )
    # Test the writer
    def test_solr_downloader(
        self,
        mock_solr_generator,
        batch_solr_generator_params,
        expected_format,
        tmp_path,
    ):
        # Define the data generator and path to the temporary file to write
        solr_gen = mock_solr_generator
        path = Path(tmp_path)
        file = "test." + expected_format
        test_file = path / file

        # Call the tested function
        _solr_downloader(
            params={**batch_solr_generator_params, "wt": expected_format},
            filename=test_file,
            solr_generator=solr_gen,
        )

        # Read the downloaded file and check it contains the expected data for json and csv.
        with open(test_file, "r", encoding="UTF-8") as f:
            if expected_format == "json":
                content = json.load(f)
                assert content == [
                    {"id": 0, "number": 0},
                    {"id": 1, "number": 1},
                    {"id": 2, "number": 2},
                    {"id": 3, "number": 100},
                    {"id": 4, "number": 99},
                    {"id": 5, "number": 98},
                ]
                # Load data into a df
                test_df = pd.read_json(test_file)

            elif expected_format == "csv":
                content = f.read()

                assert content == "id,number\n0,0\n1,1\n2,2\n3,100\n4,99\n5,98\n"
                # Load data into a df
                test_df = pd.read_csv(test_file)

            # Assert the structure of the final df
            assert_frame_equal(
                test_df,
                pd.DataFrame(
                    {
                        "id": [0, 1, 2, 3, 4, 5],
                        "number": [0, 1, 2, 100, 99, 98],
                    }
                ).reset_index(drop=True),
            )

    @pytest.mark.parametrize(
        "request_format,content",
        [
            (
                "json",
                '[{"id": "1", "city": "Cape Town"},{"id": "2", "city": "Prague"}]',
            ),
            (
                "csv",
                "id,city\n1,Cape Town\n2,Prague\n",
            ),
        ],
    )
    def test_read_downloaded_file(self, request_format, content, temp_file_fixture):
        # Write the file with corresponding content
        temp_file_fixture.write_text(content)

        test_df = _read_downloaded_file(temp_file_fixture, request_format)

        # Assert the structure of the final df
        assert_frame_equal(
            test_df,
            pd.DataFrame(
                {
                    "id": [1, 2],
                    "city": ["Cape Town", "Prague"],
                }
            ).reset_index(drop=True),
        )

    def test_read_downloaded_file_memory_error(self, temp_file_fixture):
        content = "id,city\n1,Cape Town\n2,Prague\n"
        temp_file_fixture.write_text(content)

        # Create a mock that raises a memory error when called
        with patch("pandas.read_csv", side_effect=MemoryError("Mock MemoryError")):
            with pytest.raises(
                MemoryError, match="Insuficient memory to read the file."
            ):
                _ = _read_downloaded_file(temp_file_fixture, "csv")
