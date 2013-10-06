import urls
import urllib
import variables
import json
import urllib2
import requests
import urlbuilder

class GoogleCalendar:
    access_token = ""

    def __init__(self):
        pass

    #TODO:
    # * Add parameters
    def events (self, calendar_id, params = "NULL"):
        url = urls.google_api_base_url + "calendars/{calendarId}/events" + "?" + variables.access_token_parameter + "=" + self.access_token
        url = url.replace("{calendarId}", calendar_id)

        if params != "NULL":
            url = url + urlbuilder.get(params)

        f = urllib.urlopen(url)
        response = f.read()

        return json.loads(response)

    def colors (self):
        url = urls.google_api_base_url + "colors" + "?" + variables.access_token_parameter + "=" + self.access_token
        f = urllib.urlopen(url)

    def insertEvent (self, calendar_id, params):
        url = urls.google_api_base_url + "calendars/{calendarId}/events" + "?" + variables.access_token_parameter + "=" + self.access_token
        url = url.replace("{calendarId}", calendar_id)

        f = requests.post(url, data=json.dumps(params), headers={'content-type': 'application/json'})
        response = f.json()

        return response

    def deleteEvent (self, calendar_id, event_id):
        url = urls.google_api_base_url + "calendars/{calendarId}/events/{eventId}" + "?" + variables.access_token_parameter + "=" + self.access_token

        url = url.replace("{calendarId}", calendar_id)
        url = url.replace("{eventId}", event_id)

        response = requests.delete(url)

    #TODO:
    #  * Add maxResult, pageToken, minAccessRole and showHidden parameter
    def calendars (self):
        url = urls.google_api_base_url + "users/me/calendarList" + "?" + variables.access_token_parameter + "=" + self.access_token

        f = urllib.urlopen(url)
        response = f.read()

        return json.loads(response)
