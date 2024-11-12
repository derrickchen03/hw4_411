import pytest
import requests

from meal_max.utils.random_utils import get_random

RANDOM_NUMBER = .1

@pytest.fixture
def mock_random_org(mocker):
    mock_response = mocker.Mock()
    mock_response.text = f"{RANDOM_NUMBER}"
    mocker.patch("requests.get", return_value=mock_response)
    return mock_response

def test_get_random(mock_random_org):
    result = get_random()
    assert result == RANDOM_NUMBER, f"Expected randome number {RANDOM_NUMBER}, but got {result}"

    requests.get.assert_called_once_with("https://www.random.org/decimal-fractions/?num=1&dec=2&col=1&format=plain&rnd=new", timeout=5)

def test_get_random_request_failure(mocker):
    mocker.patch("requests.get", side_effect=requests.exceptions.RequestException("connection error"))
    with pytest.raises(RuntimeError, match="Request to random.org failed: connection error"):
        get_random()

def test_get_random_timeout(mocker):
    """Simulate  a timeout."""
    mocker.patch("requests.get", side_effect=requests.exceptions.Timeout)

    with pytest.raises(RuntimeError, match="Request to random.org timed out."):
        get_random()

def test_get_random_invalid_response(mock_random_org):
    """Simulate  an invalid response (non-digit)."""
    mock_random_org.text = "invalid_response"

    with pytest.raises(ValueError, match="Invalid response from random.org: invalid_response"):
        get_random()