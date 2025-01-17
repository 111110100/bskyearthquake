from atproto import Client, client_utils
from dotenv import load_dotenv
from fake_useragent import UserAgent
import arrow
import csv
import requests
import os


def check_earthquakes(magnitude: int = 5):
    """
    :param magnitude: float representing the earthquake intensity
    :return: list[dict] if there are earthquakes greater than magnitude. False otherwise.
    """
    # Make sure we use a proper User-Agent so we won't get flagged as a scraper or bot
    ua = UserAgent()

    # Make the requests
    usgs = requests.get(
        "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.csv",
        headers = {"User-Agent": ua.chrome},
        timeout = (3, 5)
    )

    # Check the result
    if usgs:
        # Convert to CSV to list of dict
        usgs_csv = csv.DictReader(usgs.text.splitlines())

        # Filter only earthquake data that has a magnitude greater than 'magnitude'
        earthquakes = [
            l
            for l in usgs_csv
            if l["type"] == "earthquake" and is_within_timeframe(l["time"], TIMEFRAME) and float(l["mag"]) > magnitude
        ]

    # Return result
    return earthquakes if earthquakes else False


def is_within_timeframe(date_str: str, seconds: int = 60):
    """
    :param date_str: A string representing the date in ISO 8601 format (e.g., "2024-11-24T07:58:36.396Z").
    :param seconds: The number of seconds to compare the date against.
    :return: True if the given date is within the specified seconds from the current date, False otherwise.
    """
    try:
        # Parse the input date string using arrow
        input_date = arrow.get(date_str).to("utc")

        # Get the current UTC date and time using arrow
        current_date = arrow.utcnow()

        # Calculate the difference in seconds
        time_difference = abs((current_date - input_date).total_seconds())

        # Check if the difference is within the specified seconds
        return time_difference <= seconds
    except arrow.parser.ParserError as e:
        print(f"Invalid date format: {e}")
        return False


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    MAG: float = float(os.getenv("MAG", 4))
    BSKYUSER: str = os.getenv("BSKYUSER", "")
    BSKYPASS: str = os.getenv("BSKYPASS", "")
    DEBUG: bool = os.getenv("DEBUG", "F")[0] in ["T", "t"]
    TIMEFRAME: int = int(os.getenv("TIMEFRAME", 60))
    WORKDIR: str = os.getenv("WORKDIR", "/opt/bskyearthquake/")

    if DEBUG:
        print(f"MAG: {MAG}")
        print(f"BSKYUSER: {BSKYUSER}")
        print(f"BSKYPASS: {BSKYPASS}")
        print(f"TIMEFRAME: {TIMEFRAME}")
        print(f"WORKDIR: {WORKDIR}")

    if not BSKYUSER or not BSKYPASS:
        raise ValueError("Environment variable BSKYUSER and/or BSKYPASS cannot be empty")

    # Check if we have earthquakes within the timeframe that has a magnitude >= MAG
    print("Fetching earthquake information from USGS...")
    earthquakes = check_earthquakes(MAG)
    if earthquakes:
        print("We got earthquakes.")
        bluesky_logged_in = False

        # Check for existing posted_to_bluesky file
        print("Checking for previously saved data posted on bluesky...")
        if not os.path.isfile(f"{WORKDIR}posted_to_bluesky.csv"):
            with open(f"{WORKDIR}posted_to_bluesky.csv", "w") as posted_to_blueskyf:
                bluesky_writer = csv.writer(posted_to_blueskyf, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                bluesky_writer.writerow(list(earthquakes[0].keys()))
        else:
            print("Already present. We'll read it.")

        # Read and load posted bluesky posts
        print("Reading previouslty posted data from bluesky...")
        posted_to_bluesky = csv.DictReader(open(f"{WORKDIR}posted_to_bluesky.csv"))
        posted_to_bluesky = [
            d
            for d in posted_to_bluesky
        ] # Convert to list

        # Prep CSV file for adding new earthquake info if needed
        print("Opening bluesky csv file in preparation for adding new lines...")
        with open(f"{WORKDIR}posted_to_bluesky.csv", "a") as posted_to_blueskyf:
            bluesky_writer = csv.writer(posted_to_blueskyf, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for earthquake in earthquakes:

                bluesky_line = ""
                bluesky_link = ""
                print("We got data for posting.")

                # Check if already posted on bluesky
                if not list(filter(lambda e: e["time"] == earthquake["time"], posted_to_bluesky)):
                    # Make readable
                    date_utc = arrow.get(earthquake["time"])
                    date_local = date_utc.humanize()
                    date_utc = date_utc.format("MMMM DD, YYYY HH:MM")
                    bluesky_line = f"Magnitude {earthquake['mag']} {earthquake['place']} on {date_utc}\n"
                    bluesky_link = f"https://www.google.com/maps/place/{earthquake['latitude']},{earthquake['longitude']}/@{earthquake['latitude']},{earthquake['longitude']},10z"
                    print(bluesky_line)
                    print(bluesky_link)

                    if not DEBUG:
                        if not bluesky_logged_in: # Login to bluesky
                            # Init bluesky client
                            print("Logging on to bluesky...")
                            client = Client()
                            client.login(BSKYUSER, BSKYPASS)
                            bluesky_logged_in = True

                        # Save to CSV
                        print("Writing to bluesky csv...")
                        bluesky_writer.writerow(earthquake.values())

                        # Post to bluesky
                        print("Posting to bluesky...")
                        tb = client_utils.TextBuilder()
                        tb.text(bluesky_line)
                        tb.link(bluesky_link, bluesky_link)
                        post = client.send_post(tb)
                        print(f"CID: {post.cid} URI: {post.uri}")
                    else:
                        print(f"DEBUG Enabled. Not posting.")
                else: # if not list(filter())...
                        print(f"SKIP POSTED: {earthquake['time']} Magnitude {earthquake['mag']} {earthquake['place']}")
    else: # if earthquake
        print(f"No earthquakes with magnitude {MAG} within {TIMEFRAME} seconds.")