import requests


class CyTaxii(object):
    """
    Class to interact with STIX/ TAXII via CyTaxii
    """

    def __init__(self, discovery_url, username, password):
        """
        Initialize values to use across class
        :param discovery_url: Enter the discovery URL
        :param username: Enter the username to auth with
        :param password: Enter the username to auth with
        """
        self.discovery_url = discovery_url
        self.auth = (username, password)
        self.headers = {
            'Content-Type': 'application/vnd.oasis.stix+json; version=2.0',
            'User-Agent': 'cyware.httpclient',
            'Accept': 'application/vnd.oasis.taxii+json; version=2.0'
        }

    def request_handler(self, method, url, json_data=None, query_params=None):
        """
        This method is used to handle all TAXII requests
        :param query_params: Any query params to pass
        :param method: Enter the HTTP method to use
        :param url: Enter the URL to make the request to
        :param json_data: Enter the json data to pass as a payload
        """
        try:
            if method == 'GET':
                response = requests.get(url=url, data=json_data, headers=self.headers, auth=self.auth,
                                        params=query_params)
            elif method == 'POST':
                response = requests.post(url=url, data=json_data, headers=self.headers, auth=self.auth,
                                         params=query_params)
            else:
                return {
                    'response': 'Unsupported Method requested',
                    'status': False,
                    'status_code': 405
                }
            headers = response.headers

            status_code = response.status_code

            if response.ok:
                response_json = response.json()
                status = True
            else:
                response_json = response.text
                status = False

        except Exception as e:
            status_code = 'EXCEPTION'
            response_json = str(e)
            status = False
            headers = None

        return {
            'response': response_json,
            'status': status,
            'status_code': status_code,
            'headers': headers
        }

    def discovery_request(self):
        """
        This method is used to make a request to the TAXII discovery URL
        """
        response = self.request_handler(method='GET', url=self.discovery_url)
        return response

    def poll_request(self, collection_id, added_after=None, object_id=None, object_type=None,
                     start_range=None, end_range=None):
        """
        This method is used to poll data from a particular collection
        :param object_type: Enter the indicator type to retrieve
        :param start_range: Enter the start range of items to receive. 0 based
        :param object_id: Enter a specific object to retrieve
        :param end_range: Enter the end range of items to receive. 0 based
        :param added_after: Enter the date to poll from, polls all data if left blank
        :param collection_id: Enter the collection ID
        """
        if not start_range:
            start_range = 0
        if not end_range:
            end_range = 100
        range = "items {0}-{1}".format(start_range, end_range)
        self.headers["Range"] = range

        discover_response = self.discovery_request()
        params = {
            'added_after': added_after,
            'match[id]': object_id,
            'match[type]': object_type
        }
        if discover_response['status_code'] == 200:
            api_root = discover_response['response']['default']
            api_root = api_root.rstrip('/')
            poll_url = "{0}/{1}/{2}/{3}/".format(api_root, "collections", collection_id, "objects")
            response = self.request_handler(method='GET', url=poll_url, query_params=params)
            return response
        else:
            return discover_response

    def collection_request(self):

        discover_response = self.discovery_request()
        if discover_response['status_code'] == 200:
            api_root = discover_response['response']['default']
            api_root = api_root.rstrip('/')
            poll_url = "{0}/{1}/".format(api_root, "collections")
            response = self.request_handler(method='GET', url=poll_url)
            return response
        else:
            return discover_response

    def get_feeds(self, collection_id, object_type, added_after=None, object_id=None, range_from=None, range_to=None):
        """
        Method to get feed of reports
        :param collection_id: Enter the collection_id to get reports from
        :param object_type: Enter the object type to get
        :param added_after: Enter a date after to get feeds
        :param object_id: Enter a specific object ID to fetch
        :param range_from: Enter the start range of items to receive. 0 based
        :param range_to: Enter the end range of items to receive. 0 based
        """
        try:
            response = self.poll_request(collection_id=collection_id, object_type=object_type, object_id=object_id,
                                         added_after=added_after, end_range=range_to, start_range=range_from)

            return response

        except Exception as e:
            return {
                "response": str(e),
                "status": False,
                "status_code": None
            }
