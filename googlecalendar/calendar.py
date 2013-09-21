import urls
import urllib
import variables
import json

class GoogleCalendar:
    access_token = ""

    def __init__(self):
        pass

    #TODO:
    # * Add parameters
    def events (self, calendar_id):
        url = urls.google_api_base_url + "calendars/{calendarId}/events" + "?" + variables.access_token_parameter + "=" + self.access_token
        url = url.replace("{calendarId}", calendar_id)

        f = urllib.urlopen(url)
        response = f.read()

        return json.loads(response)

    def colors (self):
        url = urls.google_api_base_url + "colors" + "?" + variables.access_token_parameter + "=" + self.access_token
        f = urllib.urlopen(url)

    def insertEvent (self, calendar_id, params):
        url = urls.google_api_base_url + "calendars/{calendarId}/events" + "?" + variables.access_token_parameter + "=" + self.access_token
        url = url.replace("{calendarId}", calendar_id)

        f = urllib.urlopen(url, params)
        response = f.read()

        return json.loads(response)

    def deleteEvent (self, calendar_id, event_id):
        url = urls.google_api_base_url + "calendars/{calendarId}/events/{eventId}" + "?" + variables.access_token_parameter + "=" + self.access_token

        url = url.replace("{calendarId}", calendar_id)
        url = url.replace("{eventId}", event_id)

        f = urllib.urlopen(url)
        response = f.read()

        return json.loads(response)

    #TODO:
    #  * Add maxResult, pageToken, minAccessRole and showHidden parameter
    def calendars (self):
        url = urls.google_api_base_url + "users/me/calendarList" + "?" + variables.access_token_parameter + "=" + self.access_token

        f = urllib.urlopen(url)
        response = f.read()

        return json.loads(response)
