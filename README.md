# Bluesky Earthquake Autoposting BOT
Automatically post earthquakes with magnitude 4.5 and above on Bluesky. Latitude and longitude posted and linked to Google Maps.
## See it in action
[Tremors BOT](https://bsky.app/profile/tremorsbot.bsky.social)
## Requirements
- atproto
- datetime
- python-dotenv
- fake-useragent
- arrow
- csv
- requests
- os

## Sample line from USGS csv (converted to dictionary/json)
```javascript
{
    "time": "2024-11-23T10:47:50.871Z",
    "latitude": "-2.8095",
    "longitude": "145.7107",
    "depth": "10",
    "mag": "5.2",
    "magType": "mb",
    "nst": "47",
    "gap": "41",
    "dmin": "1.821",
    "rms": "0.78",
    "net": "us",
    "id": "us6000p78j",
    "updated": "2024-11-23T11:04:04.040Z",
    "place": "193 km WSW of Lorengau, Papua New Guinea",
    "type": "earthquake",
    "horizontalError": "6.46",
    "depthError": "1.648",
    "magError": "0.097",
    "magNst": "35",
    "status": "reviewed",
    "locationSource": "us",
    "magSource": "us"
}
```