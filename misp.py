import requests


class MISP(object):
    """
    Class to interact with MISP's API towards uploading a STIX data as an event
    """

    def __init__(self, api_key, base_url, verify=False,
                 **kwargs):
        """
        Initialize the values to use across the class
        :param api_key: Enter the MISP API key
        :param base_url: Enter the MISP base URL
        :param verify: Enter if to verify SSL cert
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.verify = verify
        self.headers = {
            "Authorization": api_key,
            "Accept": "application/json",
            "content-type": "application/json"
        }

    def handler(self, method, endpoint, params=None, data=None,
                **kwargs):
        """
        Method to handle all requests across the class
        """
        try:
            url = "{0}/{1}".format(self.base_url, endpoint)

            if method == "GET":
                response = requests.get(url=url, json=data, params=params, verify=self.verify, headers=self.headers)

            elif method == "POST":
                response = requests.post(url=url, data=data, params=params, verify=self.verify, headers=self.headers)

            else:
                return {
                    "result": "Invalid Method",
                    "status": False,
                    "status_code": None
                }

            status_code = response.status_code

            if response.ok:
                if len(response.text) == 0:
                    response_text = "No response returned"
                else:
                    response_text = response.json()
                status = True

            else:
                response_text = response.text
                status = False

            return {
                "result": response_text,
                "status": status,
                "status_code": status_code
            }

        except Exception as e:
            return {
                "result": str(e),
                "status": False,
                "status_code": None
            }

    def upload_stix(self, stix_data,
                    **kwargs):
        """
        Method to upload STIX as a event on MISP
        :param stix_data: Enter the STIX data onto MISP. Must be a bundle
        """
        endpoint = "events/upload_stix/2"
        response = self.handler(method="POST", endpoint=endpoint, data=stix_data)
        return response
