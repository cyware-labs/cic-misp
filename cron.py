import time
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import credentials
import main
import argparse
import logging


def poll_indicators():
    logging.basicConfig(filename="cic.log", filemode="w", format='%(asctime)s - %(message)s', level=logging.INFO)

    initial_run = main.poll_indicators_from_ctix(taxii_discovery_url=credentials.taxii_discovery_url,
                                                 taxii_username=credentials.taxii_username,
                                                 taxii_password=credentials.taxii_password,
                                                 taxii_collection_id=credentials.taxii_collection_id,
                                                 from_date=credentials.initial_date_from,

                                                 misp_url=credentials.misp_url,
                                                 misp_api_key=credentials.misp_api)

    logging.info(initial_run)

    # response = call_poll_indicators()
    # logging.info(response)


def poll_reports():
    logging.basicConfig(filename="cic.log", filemode="w", format='%(asctime)s - %(message)s', level=logging.INFO)

    initial_run = main.poll_reports_from_ctix(taxii_discovery_url=credentials.taxii_discovery_url,
                                              taxii_username=credentials.taxii_username,
                                              taxii_password=credentials.taxii_password,
                                              taxii_collection_id=credentials.taxii_collection_id,
                                              from_date=credentials.initial_date_from,

                                              misp_url=credentials.misp_url,
                                              misp_api_key=credentials.misp_api)

    logging.info(initial_run)

    # response = call_poll_reports()
    # logging.info(response)


def call_poll_indicators():
    try:
        today = datetime.datetime.now()
        previous_date = datetime.timedelta(seconds=credentials.cron_seconds)
        subtracted_object = today - previous_date

        subtracted_object = str(subtracted_object)  # .split(" ")[0]
        response = main.poll_indicators_from_ctix(
            taxii_discovery_url=credentials.taxii_discovery_url,
            taxii_password=credentials.taxii_password,
            taxii_username=credentials.taxii_username,
            taxii_collection_id=credentials.taxii_collection_id,
            from_date=subtracted_object,
            misp_url=credentials.misp_url,
            misp_api_key=credentials.misp_api)

        return response

    except Exception as e:
        return str(e)


def call_poll_reports():
    try:
        today = datetime.datetime.now()
        previous_date = datetime.timedelta(seconds=credentials.cron_seconds)
        subtracted_object = today - previous_date

        subtracted_object = str(subtracted_object)  # .split(" ")[0]

        response = main.poll_reports_from_ctix(
            taxii_discovery_url=credentials.taxii_discovery_url,
            taxii_password=credentials.taxii_password,
            taxii_username=credentials.taxii_username,
            taxii_collection_id=credentials.taxii_collection_id,
            from_date=subtracted_object,
            misp_url=credentials.misp_url,
            misp_api_key=credentials.misp_api)

        return response

    except Exception as e:
        return str(e)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--option",
                        help="Enter the option to run the script on. Options available: poll_indicators or poll_reports",
                        required=True)

    scheduler = BackgroundScheduler()
    args = parser.parse_args()

    if args.option == "poll_reports":
        poll_reports()
        scheduler.add_job(call_poll_reports, 'interval', seconds=credentials.cron_seconds)
        scheduler.start()

    elif args.option == "poll_indicators":
        poll_indicators()
        scheduler.add_job(call_poll_indicators, 'interval', seconds=credentials.cron_seconds)
        scheduler.start()

    else:
        raise SyntaxError("Enter valid option to run the script on. Options available: poll_indicators or poll_reports")

    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
