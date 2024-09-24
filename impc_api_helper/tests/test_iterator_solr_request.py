import pytest
from pathlib import Path
from unittest.mock import patch, call, MagicMock
from impc_api_helper.iterator_solr_request_2 import batch_solr_request, _batch_solr_generator, solr_request, _batch_to_df
import io
import pandas as pd
from pandas.testing import assert_frame_equal
from .test_helpers import check_url_status_code_and_params


# Fixture containing the core
@pytest.fixture
def core():
    return 'test_core'

class TestBatchSolrRequest():

    # Fixture containing the params of a normal batch_solr_request
    @pytest.fixture
    def common_params(self):
        return {"start": 0, "rows": 10000, "wt": "json"}
    
    # Fixture containing the solr_request function mock
    # We will be mocking solr_request with different numbers of numFound, therefore it is passed as param
    @pytest.fixture
    def mock_solr_request(self, request):
        with patch('impc_api_helper.iterator_solr_request_2.solr_request') as mock:
            # Mock expected return content of the solr_request (numFound and _)
            mock.return_value = (request.param, pd.DataFrame())
            yield mock

    # Pytest fixture mocking _batch_to_df
    @pytest.fixture
    def mock_batch_to_df(self):
        with patch('impc_api_helper.iterator_solr_request_2._batch_to_df') as mock:
            yield mock

    # Parameters to determine the numFound of mock_solr_request
    @pytest.mark.parametrize("mock_solr_request", [10000], indirect=True)
    def test_batch_solr_request_no_download_small_request(self, mock_solr_request, core, common_params, capsys, mock_batch_to_df):
        
        # Call your function that uses the mocked request
        # Set up mock_solr_request values
        result = batch_solr_request(core, params=common_params, 
                                    download=False)
        
        # # Assert the mock was called with the expected parameters (start = 0, rows = 0) despite calling other values.
        mock_solr_request.assert_called_with(
        core=core, 
        params={**common_params, "start": 0, "rows": 0, "wt": "json"}, 
        silent=True
        )

        # Capture stoud
        num_found = mock_solr_request.return_value[0]
        captured = capsys.readouterr()
        assert captured.out == f"Number of found documents: {num_found}\n"

        # Check _batch_to_df was called
        mock_batch_to_df.assert_called_once()


    # Set mock_solr_request to return a large numFound
    @pytest.mark.parametrize("mock_solr_request", [1000001], indirect=True)
    # Parameter to test 4 cases: when user selects 'y' or 'n' upon large download warning.
    @pytest.mark.parametrize("user_input,expected_outcome", [
        ('y', 'continue'),
        ('', 'continue'),
        ('n', 'exit'),
        ('exit', 'exit')
    ])
    def test_batch_solr_request_no_download_large_request(self, core, common_params, capsys, monkeypatch, mock_batch_to_df, mock_solr_request, user_input, expected_outcome):
        # Monkeypatch the input() function with parametrized user input
        monkeypatch.setattr('builtins.input', lambda _: user_input)

        # When user selects 'n', exit should be triggered.
        if expected_outcome == 'exit':
            with pytest.raises(SystemExit):
                batch_solr_request(core, params=common_params, download=False, batch_size=5000)
        else:
            result = batch_solr_request(core, params=common_params, download=False, batch_size=5000)

        # Capture the exit messages 
        captured = capsys.readouterr()
        
        # Assertions for continue case
        num_found = mock_solr_request.return_value[0]

        assert f"Number of found documents: {num_found}" in captured.out

        if expected_outcome == 'continue': 
            assert "Your request might exceed the available memory. We suggest setting 'download=True' and reading the file in batches" in captured.out
            mock_batch_to_df.assert_called_once_with('test_core', {'start': 0, 'rows': 5000, 'wt': 'json'}, 1000001)

        # Assertion for exit case
        elif expected_outcome == 'exit':
            assert "Exiting gracefully" in captured.out
            mock_batch_to_df.assert_not_called()



    # TEST DOWNLOAD TRUE
    # Fixture mocking the activity of _batch_solr_generator
    @pytest.fixture
    def mock_batch_solr_generator(self):
        with patch('impc_api_helper.iterator_solr_request_2._batch_solr_generator') as mock:
            yield mock

    @pytest.fixture
    def mock_solr_downloader(self, tmp_path):
        with patch('impc_api_helper.iterator_solr_request_2._solr_downloader') as mock:
            temp_dir = Path(tmp_path) / 'temp_dir'
            temp_dir.mkdir()
            yield mock


    # Mock response for test containing more than 2,000,000 docs
    @pytest.mark.parametrize("mock_solr_request", [2000000], indirect=True)
    # Parametrized decorator to simulate reading a json and csv files
    @pytest.mark.parametrize(
        "params_format, format, file_content, expected_columns",
        [
            ({"start": 0, "rows": 2000000, "wt": "json"},"json", '{"id": "1", "city": "Houston"}\n{"id": "2", "city": "Prague"}\n', ['id', 'city']),
            ({"start": 0, "rows": 2000000, "wt": "csv"},"csv", 'id,city\n1,Houston\n2,Prague\n', ['id', 'city'])
        ]
    )
    # Test download = True
    def test_batch_solr_request_download_true(self, core, capsys, mock_solr_request, mock_batch_solr_generator, mock_solr_downloader, tmp_path, common_params, params_format, format, file_content, expected_columns):

        # Create temporary files for the test
        temp_dir = tmp_path / 'temp_dir'
        filename = f"{core}.{format}"
        temp_file = temp_dir / filename
        temp_file.write_text(file_content)
        

        # First we call the function
        # We patch solr_request to get the number of docs
        result = batch_solr_request(core, params=params_format, download=True, path_to_download=temp_dir)
        num_found = mock_solr_request.return_value[0]

        # Check _batch_solr_generator gets called once with correct args
        mock_batch_solr_generator.assert_called_once_with(core, params_format, num_found)
        
        # Check _solr_downloader gets called once with correct args
        mock_solr_downloader.assert_called_once_with(params_format, temp_file, mock_batch_solr_generator.return_value)

        # Check the print statements
        captured = capsys.readouterr()
        assert f"Number of found documents: {num_found}" in captured.out
        assert "Showing the first batch of results only" in captured.out

        # Check a pd was created and its contents
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result.columns) == expected_columns
        assert result.loc[0,'id'] == 1
        assert result.loc[0,'city'] == 'Houston'
        assert result.loc[1,'id'] == 2
        assert result.loc[1,'city'] == 'Prague'
        

    # Mock params
    @pytest.fixture
    def multiple_field_params(self):
        return {
            "q": "*:*",
            "rows": 0,
            "start": 0,
            "field_list":['"orange"','apple','*berry'],
            "field_type": "fruits",
            "wt":"json"

        }
    # Mock response for test containing more than 2,000,000 docs
    @pytest.mark.parametrize("mock_solr_request", [(2000000),(10000)], indirect=True)

    @pytest.mark.parametrize(
        "download_bool",
        [
            (True),
            (False)
        ],
    )
    # @pytest.mark.skip(reason="no way of currently testing this")
    def test_batch_solr_request_multiple_fields(self, core, multiple_field_params, capsys, mock_solr_request, mock_batch_solr_generator, download_bool, monkeypatch, mock_batch_to_df, mock_solr_downloader, tmp_path):
        #  This test should make sure the request is formatted properly. Regardless of going to downloads or to _batch_to_df
        
        # Get num_found
        num_found = mock_solr_request.return_value[0]
        # In the case where download=False and numFound is > 1,000,001 we pass 'y' in this test case. 
        if not download_bool and num_found == 2000000:
            monkeypatch.setattr('builtins.input', lambda _: 'y')
        
        # Call test function
        # If downloads create a temporary file and call with the path_to_download
        if download_bool:
            temp_dir = tmp_path / 'temp_dir'
            temp_file = temp_dir / f"{core}.json"
            temp_file.write_text('{"id": "1", "city": "Cape Town"}\n')
            result = batch_solr_request(core, params=multiple_field_params, download=download_bool, path_to_download=temp_dir)
        else:
            # Otherwise, call without the path_to_download
            result = batch_solr_request(core, params=multiple_field_params, download=download_bool)
    
        # Check output which should be equal for both.
        captured = capsys.readouterr()
        assert f"Number of found documents: {num_found}" in captured.out
        assert 'Queried field: fruits:("orange" OR apple OR *berry)' in captured.out

        # If download was true, check subsequent functions were executed 
        if download_bool:
            assert "Showing the first batch of results only" in captured.out
            # Check _batch_solr_generator gets called once with correct args
            mock_batch_solr_generator.assert_called_with(core, multiple_field_params, num_found)
            
            # Check _solr_downloader gets called once with correct args
            mock_solr_downloader.assert_called_once_with(multiple_field_params, temp_file, mock_batch_solr_generator.return_value)


        # Otherwise, use the 'y' input at the start of the test and make sure the required function is executed. 
        if not download_bool and num_found == 2000000:
            assert "Your request might exceed the available memory. We suggest setting 'download=True' and reading the file in batches" in captured.out
            # Check _batch_to_df was called with correct params
            mock_batch_to_df.assert_called_once_with(core, multiple_field_params, num_found)

# Have helper functions in a different class to separate fixtures and parameters
class TestHelpersSolrBatchRequest():
    # Define a generator to produce DF's dynamically
    def dataframe_generator(self):
        """ Generator to produce dataframes dynamically (row by row)/

        Yields:
            pd.DataFrame: Dataframe with one row of data
        """
        # Values for the dataframes
        animals = ['Bull', 'Elephant', 'Rhino', 'Monkey', 'Snake']
        # Construct the dataframe and yield it
        for i, a in enumerate(animals): 
            yield pd.DataFrame(
               {
                    'id': [i],
                    'animal': [a]
                }
            )
        
    # Fixture containing the solr_request function mock
    # Num_found is passed dynamically as params in the test
    # The DF is returned dynamically using the generator
    @pytest.fixture
    def mock_solr_request_generator(self, request):
        """ Patches solr_request for _batch_to_df _batch_solr_generator producing a df dynamically.
            Creates a df in chunks (row by row) mocking incoming batches of responses. 
        """
        with patch('impc_api_helper.iterator_solr_request_2.solr_request') as mock:
            df_generator = self.dataframe_generator()
            def side_effect(*args, **kwargs):
                df = next(df_generator)
                return request.param, df
            mock.side_effect = side_effect
            yield mock

    # Fixture containing the params of a normal batch_solr_request
    @pytest.fixture
    def batch_params(self, rows):
        return {"start": 0, "rows": rows, "wt": "json"}
    
    @pytest.fixture
    def num_found(self, request):
        return request.param

    # Parameters to be passsed to the test: the num_found for mock_solr_request_generator, the num_found separately, and rows (batch_size).
    # Note num_found is returned by solr_request, when we access it using the generator function, it causes issues.
    # Hence, we pass num_found separately as a fixture. 
    @pytest.mark.parametrize("mock_solr_request_generator,num_found,rows", [
        (50000, 50000, 10000),
        (5, 5, 1),
        (25000, 25000, 5000)
                                                                            ],
        indirect=['mock_solr_request_generator'])
    
    def test_batch_to_df(self, core, batch_params, num_found, mock_solr_request_generator, rows):
        # Call the tested function
        df = _batch_to_df(core, batch_params, num_found)

        # Assert solr_request was called with the expected params and increasing start 
        expected_calls = [
            call(core=core, params={**batch_params, 'start': i * rows, 'rows': rows}, silent=True) for i in range(5)
        ]
        mock_solr_request_generator.assert_has_calls(expected_calls)

        # Assert the structure of the final df 
        assert_frame_equal(df, pd.DataFrame(
            {
                'id': [0, 1, 2, 3, 4],
                'animal': ['Bull', 'Elephant', 'Rhino', 'Monkey', 'Snake']
            }
        ).reset_index(drop=True))

        
    # Test _batch_solr_generator
    # This function uses the requests module so we need to patch it
    # Main outcomes: 
        # The data is yielded back as json DONE
        # The data is yielded back as text DONE
        # The error raises and exception DONE 
        # The requests module is called multiple times
        # The start param is increased by batch_size
        # The URL, and compount url should be checked.
    
    # Fixture to mock the requests module
    @pytest.fixture
    def mock_requests_get(self, request):
        with patch('impc_api_helper.iterator_solr_request_2.requests.get') as mock_get:
            # Capture the format of the response
            wt = request.param["wt"]
            mock_get.return_value.format = wt
           
            # Get the status code and
            mock_get.return_value.status_code = request.param["status_code"]

             # Get "response" data according to format
            if wt == "json":
                mock_get.return_value.json.return_value = request.param["response"]
            
            elif wt == "csv":
                mock_get.return_value.text = request.param["response"]
            
            yield mock_get

    # Fixture containing the params for batch_solr_generator
    @pytest.fixture
    def batch_solr_generator_params(self):
        return {"start": 0, "rows": 2}
    @pytest.mark.parametrize(
        "mock_requests_get",
        [ 
            ({
                "status_code": 200,
                "response": {"response": {
                    "docs": [
                        {"id": "Gibson"},
                        {"id": "Ibanez"},
                        {"id": "Schecter"},
                        {"id": "PRS"}
                    ]            
                }},
                "wt": "json"
            }),
            ({
                "status_code": 200,
                "response": "id\nGibson\nIbanez\nSchecter\nPRS",
                "wt": "csv"
            })
        ],
        indirect=['mock_requests_get']
    )
    def test_batch_solr_generator(self, core, batch_solr_generator_params, mock_requests_get):
        
        # Define num_found
        num_results = 4
        # Define the wt and batch_size param for the test
        batch_solr_generator_params["wt"] = mock_requests_get.return_value.format
        batch_solr_generator_params["rows"] = 1

        # Create the generator
        result = _batch_solr_generator(core, batch_solr_generator_params, num_results)

        # Assertions for json data
        if batch_solr_generator_params["wt"] == "json":
            assert next(result) == [
                    {"id": "Gibson"},
                    {"id": "Ibanez"},
                    {"id": "Schecter"},
                    {"id": "PRS"}
            ]
        # Assertions for csv
        elif batch_solr_generator_params["wt"] == "csv":
            assert next(result) == "id\nGibson\nIbanez\nSchecter\nPRS"

        # General assertions
        # Checks the url, status code, and params called are as expected.
        check_url_status_code_and_params(
            mock_response=mock_requests_get,
            expected_status_code=200,
            expected_core=core,
            expected_params=batch_solr_generator_params,
        )

    # Simpler approach to test when status code is 404
    @pytest.fixture
    def mock_requests_get_error(self, request):
        with patch('impc_api_helper.iterator_solr_request_2.requests.get') as mock_get:
            mock_get.return_value.status_code = request.param
            yield mock_get

    # Set up test for _batch_solr_generator when status code is 404
    @pytest.mark.parametrize("mock_requests_get_error", [404, 500], indirect=['mock_requests_get_error'])
    def test_batch_solr_generator_error(self, core, batch_solr_generator_params, mock_requests_get_error):
        # Get status code:
        status_code = mock_requests_get_error.return_value.status_code
        # Call the generator and expect an exception to be raised
        # Note the num_found is passed but the number itself does not matter
        # Note list() is needed so that the generator is iterated otherwise exception is never reached.
        with pytest.raises(Exception, match=f"Request failed. Status code: {status_code}"):
            _ = list(_batch_solr_generator(core=core, params=batch_solr_generator_params, num_results=4))
            


    # TODO:
    # _solr_downloader
