from time import sleep
import traceback

from praw.exceptions import APIException
from prawcore.exceptions import BadRequest, ResponseException, RequestException
from requests.exceptions import ConnectionError

# from ..models import Logger

def retry(action):
    def actionWithRetry(*args, **kwargs):
        '''Perform the given action. If an exception is raised, retry every ten seconds

        @param throwOnPayloadTooLarge boolean If a 413 error is caught, throw it instead of retrying (default False)
        Return the return value of the action, if any
        '''

        failCount = 0

        while True:
            try:
                result = action(*args, **kwargs)

                # if failCount > 0:
                #     Logger.warn("Action succeeded after previously failing", {
                #         "action": action.__name__,
                #         "failCount": failCount,
                #     })

                return result

            except BadRequest as e:
                # Don't keep trying if we get a bad request
                # This is likely caused by deleted accounts so we can safely ignore them
                # Logger.warn("Action failed with HTTP status 400. Returning...", {
                #     "action": action.__name__,
                #     "traceback": traceback.format_exc(),
                #     "responseText": e.response.text,
                #     "responseUrl": e.response.url,
                #     "requestUrl": e.response.request.url,
                #     "requestBody": e.response.request.body,
                # })
                return

            except APIException as e:
                if e.error_type == "TOO_LONG" and kwargs.get('throwOnPayloadTooLarge', False):
                    # Logger.warn("Action failed with HTTP status 413, raising", { "action": action.__name__ })
                    raise e

                failCount += 1

                if failCount == 1:
                    pass
                    # Logger.error(traceback.format_exc())

                sleep(10)
                continue

            except (ConnectionError, ResponseException, RequestException) as e:
                failCount += 1

                if failCount == 1:
                    pass
                    # Logger.error(traceback.format_exc())

                sleep(10)
                continue

    return actionWithRetry
