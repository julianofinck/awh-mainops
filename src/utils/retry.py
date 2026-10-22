import logging
import random
import time

import requests

log = logging.getLogger(__name__)


def mit_retry(func, *args, **kwargs):
    delay = 5.0
    max_delay = 600.0  # 10 minutes

    while True:
        try:
            return func(*args, **kwargs)

        except requests.HTTPError as e:
            status = e.response.status_code if e.response else None

            if status not in (500, 502, 503, 504):
                raise

            if delay > max_delay:
                raise

            log.warning(
                "HTTP %s. Retrying in %.1fs...",
                status,
                delay,
            )

            time.sleep(delay * random.uniform(0.9, 1.1))
            delay *= 1.5

        except (
            requests.Timeout,
            requests.ConnectionError,
        ):
            if delay > max_delay:
                raise

            log.warning(
                "Connection error. Retrying in %.1fs...",
                delay,
            )

            time.sleep(delay * random.uniform(0.9, 1.1))
            delay *= 1.5
