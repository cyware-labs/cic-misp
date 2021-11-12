import json
import requests
import urllib3
import credentials
import datetime
import argparse
import math
import sys

from dateutil import parser
from stix2.v20 import Bundle, Report
from cytaxii import CyTaxii
from misp import MISP

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def list_taxii_collections(taxii_discovery_url: str,
                           taxii_username: str,
                           taxii_password: str):
    """
    This method is used to list all collections in a TAXII server enabled for the user
    """
    try:
        taxii_object = CyTaxii(discovery_url=taxii_discovery_url,
                               username=taxii_username,
                               password=taxii_password)
        result = taxii_object.collection_request()

    except Exception as e:
        result = str(e)

    return result


def poll_indicators_from_ctix(taxii_discovery_url: str,
                              taxii_username: str,
                              taxii_password: str,
                              taxii_collection_id: str,
                              from_date: str,

                              misp_url: str,
                              misp_api_key: str):
    """
    This method is used to poll indicators from CTIX, package these indicators into a report,
    and push those packaged indicator to MISP

    :param taxii_discovery_url: Enter the TAXII discovery URL to connect to
    :param taxii_username:  Enter the TAXII username to authenticate with
    :param taxii_password: Enter the TAXII password to authenticate with
    :param taxii_collection_id: Enter the TAXII collection ID which houses the indicators
    :param misp_url: Enter the MISP URL to push the data to
    :param misp_api_key: Enter the MISP API key to authenticate to MISP with
    :param from_date: Enter the date, to poll data from. Form YYYY-MM-DD
    :return: Collection of MISP responses
    """
    try:
        response = []

        taxii_object = CyTaxii(discovery_url=taxii_discovery_url,
                               username=taxii_username,
                               password=taxii_password)
        misp_object = MISP(base_url=misp_url, api_key=misp_api_key)

        initial_taxii_response = taxii_object.get_feeds(collection_id=taxii_collection_id,
                                                        object_type="indicator",
                                                        added_after=from_date)
        from_list = []
        to_list = []

        if initial_taxii_response["status"] and len(initial_taxii_response["response"]["objects"]) != 0:

            # Flush the existing initial objects, to avoid duplications while sequentially overwriting pagination
            initial_taxii_response["response"]["objects"] = []

            to_range = initial_taxii_response["headers"].get("Content-Range")
            to_range = int(str(to_range).split("/")[1])

            if to_range > 1000:
                chunk_number = to_range / 1000
                chunk_number = math.ceil(chunk_number)
                from_no = 0
                tmp = 0

                for number in range(1, chunk_number + 1):
                    to_number = number * 1000
                    to_list.append(to_number)
                    from_no = tmp
                    from_list.append(from_no)
                    tmp = to_number

                for from_range, to_range in zip(from_list, to_list):
                    paginated_taxii_response = taxii_object.get_feeds(collection_id=taxii_collection_id,
                                                                      object_type="indicator",
                                                                      added_after=from_date,
                                                                      range_from=from_range,
                                                                      range_to=to_range)

                    if paginated_taxii_response["status"]:
                        initial_taxii_response["response"]["objects"].extend(
                            paginated_taxii_response["response"]["objects"])

                    else:
                        raise SyntaxError(paginated_taxii_response)
            else:
                paginated_taxii_response = taxii_object.get_feeds(collection_id=taxii_collection_id,
                                                                  object_type="indicator",
                                                                  added_after=from_date,
                                                                  range_from=0,
                                                                  range_to=1000)

                if paginated_taxii_response["status"]:
                    initial_taxii_response["response"]["objects"].extend(
                        paginated_taxii_response["response"]["objects"])

                else:
                    raise SyntaxError(paginated_taxii_response)

        else:
            raise SyntaxError(initial_taxii_response)

        for indicator in initial_taxii_response["response"]["objects"]:

            indicator_id = indicator.get("id", None)
            indicator_name = indicator.get("name", None)
            created_date = indicator.get("created", None)

            if created_date:
                created_date = parser.parse(created_date)

            if not created_date:
                created_date = datetime.datetime.now()

            report = Report(type="report", name=indicator_name, object_refs=[indicator_id], published=created_date,
                            labels=["indicator"], allow_custom=True)

            init_bundle = Bundle(indicator, report, allow_custom=True).serialize(pretty=True)

            misp_response = misp_object.upload_stix(stix_data=init_bundle)
            response.append(misp_response)

    except Exception as e:
        response = str(e)

    return response


def poll_reports_from_ctix(taxii_discovery_url: str,
                           taxii_username: str,
                           taxii_password: str,
                           taxii_collection_id: str,
                           from_date: str,

                           misp_url: str,
                           misp_api_key: str):
    """
    This method is used to poll reports from CTIX, and push those packaged indicator to MISP

    :param taxii_discovery_url: Enter the TAXII discovery URL to connect to
    :param taxii_username:  Enter the TAXII username to authenticate with
    :param taxii_password: Enter the TAXII password to authenticate with
    :param taxii_collection_id: Enter the TAXII collection ID which houses the indicators
    :param misp_url: Enter the MISP URL to push the data to
    :param misp_api_key: Enter the MISP API key to authenticate to MISP with
    :param from_date: Enter the date, to poll data from. Form YYYY-MM-DD
    :return: Collection of MISP responses
    """
    try:
        response = []
        taxii_object = CyTaxii(discovery_url=taxii_discovery_url,
                               username=taxii_username,
                               password=taxii_password)
        misp_object = MISP(base_url=misp_url, api_key=misp_api_key)

        initial_taxii_response = taxii_object.get_feeds(collection_id=taxii_collection_id,
                                                        object_type="report",
                                                        added_after=from_date)

        from_list = []
        to_list = []

        if initial_taxii_response["status"] and len(initial_taxii_response["response"]["objects"]) != 0:
            # Flush the existing initial objects, to avoid duplications while sequentially overwriting pagination
            initial_taxii_response["response"]["objects"] = []

            to_range = initial_taxii_response["headers"].get("Content-Range")
            to_range = int(str(to_range).split("/")[1])

            if to_range > 1000:

                chunk_number = to_range / 1000
                chunk_number = math.ceil(chunk_number)
                from_no = 0
                tmp = 0

                for number in range(1, chunk_number + 1):
                    to_number = number * 1000
                    to_list.append(to_number)
                    from_no = tmp
                    from_list.append(from_no)
                    tmp = to_number

                for from_range, to_range in zip(from_list, to_list):
                    paginated_taxii_response = taxii_object.get_feeds(collection_id=taxii_collection_id,
                                                                      object_type="report",
                                                                      added_after=from_date,
                                                                      range_from=from_range,
                                                                      range_to=to_range)

                    if paginated_taxii_response["status"]:
                        initial_taxii_response["response"]["objects"].extend(
                            paginated_taxii_response["response"]["objects"])

                    else:
                        raise SyntaxError(paginated_taxii_response)

            else:
                paginated_taxii_response = taxii_object.get_feeds(collection_id=taxii_collection_id,
                                                                  object_type="report",
                                                                  added_after=from_date,
                                                                  range_from=0,
                                                                  range_to=1000)

                if paginated_taxii_response["status"]:
                    initial_taxii_response["response"]["objects"].extend(
                        paginated_taxii_response["response"]["objects"])

                else:
                    raise SyntaxError(paginated_taxii_response)

        else:
            raise SyntaxError(initial_taxii_response)

        for report in initial_taxii_response["response"]["objects"]:
            report_objects = []

            init_bundle = Bundle(report, allow_custom=True)
            object_refs = report.get("object_refs", None)

            if object_refs:

                for ref in object_refs:

                    flag = True

                    if str(ref).startswith("report") or str(ref).startswith("indicator"):
                        flag = False

                    poll_response = taxii_object.poll_request(collection_id=credentials.taxii_collection_id,
                                                              object_id=ref)
                    report_objects.extend(poll_response["response"]["objects"])

                    if flag:

                        type = poll_response["response"]["objects"][0]["type"]
                        name = poll_response["response"]["objects"][0].get("name", None)

                        if not name:
                            name = poll_response["response"]["objects"][0].get("x_title", None)

                        form = "{0}:{1}".format(type, name)
                        init_bundle["objects"][0]["labels"].append(form)

            init_bundle["objects"].extend(report_objects)
            init_bundle = init_bundle.serialize(pretty=True)

            misp_response = misp_object.upload_stix(stix_data=init_bundle)
            response.append(misp_response)

    except Exception as e:
        response = str(e)

    return response


if __name__ == '__main__':

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--option",
                            help="Enter the option to run the script on. Options available: list_collections, "
                                 "poll_indicators or poll_reports",
                            required=True)

    args = arg_parser.parse_args(sys.argv[1:])

    if args.option == "list_collections":
        response = list_taxii_collections(
            taxii_discovery_url=credentials.taxii_discovery_url,
            taxii_username=credentials.taxii_username,
            taxii_password=credentials.taxii_password
        )

    elif args.option == "poll_indicators":
        response = poll_indicators_from_ctix(
            taxii_discovery_url=credentials.taxii_discovery_url,
            taxii_username=credentials.taxii_username,
            taxii_password=credentials.taxii_password,
            taxii_collection_id=credentials.taxii_collection_id,
            from_date=credentials.initial_date_from,

            misp_url=credentials.misp_url,
            misp_api_key=credentials.misp_api
        )
    elif args.option == "poll_reports":
        response = poll_reports_from_ctix(
            taxii_discovery_url=credentials.taxii_discovery_url,
            taxii_username=credentials.taxii_username,
            taxii_password=credentials.taxii_password,
            taxii_collection_id=credentials.taxii_collection_id,
            from_date=credentials.initial_date_from,

            misp_url=credentials.misp_url,
            misp_api_key=credentials.misp_api
        )
    else:
        raise SyntaxError("Enter valid option to run the script on. "
                          "Options available: poll_indicators or poll_reports or list_collections")

    print(response)
