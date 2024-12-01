from atproto import Client
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
        values = [l for l in usgs_csv if l["type"] == "earthquake" and float(l["mag"]) > magnitude]

    # Return result
    return values if values else False


def is_within_timeframe(date_str, seconds: int = 60):
    """
    :param date_str: A string representing the date in ISO 8601 format (e.g., "2024-11-24T07:58:36.396Z").
    :param seconds: The number of seconds to compare the date against.
    :return: True if the given date is within the specified seconds from the current date, False otherwise.
    """
    try:
        # Parse the input date string using arrow
        input_date = arrow.get(date_str)
        
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
    load_dotenv()
    MAG: float = float(os.getenv("MAG", 5))
    BSKYUSER: str = os.getenv("BSKYUSER", "")
    BSKYPASS: str = os.getenv("BSKYPASS", "")
    DEBUG: bool = os.getenv("DEBUG", "F")[0] in ["T", "t"]
    TIMEFRAME: int = int(os.getenv("TIMEFRAME", 60))
    if not BSKYUSER or not BSKYPASS:
       raise ValueError("Environment variable BSKYUSER and/or BSKYPASS cannot be empty")
    earthquakes = check_earthquakes(MAG)
    if earthquakes:
        client = Client()
        client.login(BSKYUSER, BSKYPASS)
        with open("tremors.txt", "a") as f:
            for earthquake in earthquakes:
                lines = ""
                if is_within_timeframe(earthquake["time"], TIMEFRAME):
                    # Make readable
                    date_utc = arrow.get(earthquake["time"])
                    date_local = date_utc.humanize()
                    date_utc = date_utc.format("MMMM DD, YYYY HH:MM")
                    lines += f"Magnitude {earthquake['mag']} {earthquake['place']} on {date_utc}\n"
                    lines += f"Map: https://maps.google.com/?q={earthquake['latitude']},{earthquake['longitude']}\n"
                    print(lines)
                    f.write(lines)
                    # Post to Bluesky
                    if not DEBUG:
                        post = client.send_post(text=lines)
                        print(f"CID: {post.cid} URI: {post.uri}")
                else:
                    print(f"SKIP: Magnitude {earthquake['mag']} {earthquake['place']} on {earthquake['time']}")