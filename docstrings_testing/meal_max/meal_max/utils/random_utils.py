import logging
import requests

from meal_max.utils.logger import configure_logger

logger = logging.getLogger(__name__)
configure_logger(logger)


def get_random() -> float:
    """
    Fetches a random deciaml number from random.org with two decimal places

    The function sends a GET request to random.org to retrieve a single random 
    decimal fraction formatted to two decimal places.The response is parsed and converted to a float. If the request
    is unsuccessful or if the response cannot be parsed as a float, an execption is raised.

    Raises:
        ValueError: if the response from random.org is not a valid float
        RuntimeError: if the request to the random.org fails or times out

    Returns:
        float: A random decimal number between 0 and 1 with two decimal places
    """
    url = "https://www.random.org/decimal-fractions/?num=1&dec=2&col=1&format=plain&rnd=new"

    try:
        # Log the request to random.org
        logger.info("Fetching random number from %s", url)

        response = requests.get(url, timeout=5)

        # Check if the request was successful
        response.raise_for_status()

        random_number_str = response.text.strip()

        try:
            random_number = float(random_number_str)
        except ValueError:
            raise ValueError("Invalid response from random.org: %s" % random_number_str)

        logger.info("Received random number: %.3f", random_number)
        return random_number

    except requests.exceptions.Timeout:
        logger.error("Request to random.org timed out.")
        raise RuntimeError("Request to random.org timed out.")

    except requests.exceptions.RequestException as e:
        logger.error("Request to random.org failed: %s", e)
        raise RuntimeError("Request to random.org failed: %s" % e)
