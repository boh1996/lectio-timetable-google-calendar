import urllib2
import time as timeLib
from time import mktime
from datetime import datetime
from pytz import timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from googleauth import google_oauth
import config
import calendar
from googlecalendar import calendar as GoogleCalendarObject
import itertools
from datetime import *
from bs4 import BeautifulSoup, SoupStrainer

# Creates the Calendar event title
def createTitle (localEvent):
    return "%s - %s - %s" % (localEvent["group"].decode("utf8"), localEvent["teacher"].decode("utf8"), localEvent["room"].decode("utf8"))

# Compares the local event with the Google Event, using start date, end date and event summary/title
def sameEvent (googleEvent, localEvent):
    timezone("Europe/Copenhagen")
    startTuple = localEvent["startDateTime"].utctimetuple()
    endTuple = localEvent["endDateTime"].utctimetuple()
    googleStartTuple = datetime.strptime(googleEvent["start"]["dateTime"][:-6], "%Y-%m-%dT%H:%M:%S").utctimetuple()
    googleEndTuple = datetime.strptime(googleEvent["end"]["dateTime"][:-6], "%Y-%m-%dT%H:%M:%S").utctimetuple()

    return (
        calendar.timegm(googleStartTuple) == calendar.timegm(startTuple) and
        calendar.timegm(googleEndTuple) == calendar.timegm(endTuple) and
        googleEvent["summary"] == createTitle(localEvent)
    )

# Crete the database Engine
engine = create_engine("%s://%s:%s@%s/%s" % (config.database, config.db_user, config.db_password, config.db_host, config.db_database))

# Create a Session
Session = sessionmaker(bind=engine)
session = Session()

# Create the tasks table, if it doesn't exist
session.execute("CREATE TABLE IF NOT EXISTS `tasks` ( `id` int(11) NOT NULL AUTO_INCREMENT, `calendar_id` varchar(255) DEFAULT NULL, `last_updated` varchar(255) DEFAULT NULL,`simplify` varchar(2) DEFAULT NULL , `google_id` varchar(80) DEFAULT NULL, `lectio_id` varchar(80) DEFAULT NULL, `school_id` varchar(45) DEFAULT NULL, PRIMARY KEY (`id`)) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=latin1")

# Fetch the tasks to run from the database
tasks = session.execute("SELECT * FROM tasks")

# Get the datetime for the current moment, with Europe/Copenhagen as a timezone
currentWeekDateTime = datetime.date(datetime.now(timezone('Europe/Copenhagen')))

# Get the current week number
currentWeek = int(currentWeekDateTime.strftime("%U"))+1

# The number of weeks to run
numberOfWeeks = 4

try:
    numberOfWeeks = config.numberOfWeeks
except BaseException:
    pass

# The currentWeek+numberOfWeeks, it can be larger then the max number of weeks
endWeek = currentWeek+numberOfWeeks

# If the year has changed
yearChange = False

# The current year
startYear = int(currentWeekDateTime.strftime("%Y"))

# Initialize the weeks variable
weeks = []

# Get the max number of weeks in the current year
maxWeeks = int(datetime.strptime(str(startYear) + "-12-31", "%Y-%m-%d").strftime("%U"))

# Fill content into the 'weeks' list
for i in range(currentWeek, endWeek):

    # If the current number is larger then the maximum number of weeks, calculate the new week
    if i > maxWeeks:
        weeks.append(currentWeek+numberOfWeeks-i)
    else:
        weeks.append(i)

# If the year has changed, set the year changed to true
if currentWeek+numberOfWeeks > maxWeeks:
    yearChange = True

# Debug info
print weeks

# Loop through  the tasks to run
for task in tasks:

    # Loop through the weeks for each task
    for x in weeks:

        # If the year has to be incremented, increment it
        if x < currentWeek:
            year = startYear+1
        else:
            year = startYear

        # Fetch the Google Auth information from the database
        tokenQuery = session.execute('SELECT * FROM user WHERE user_id="%s"' % (task["google_id"]))

        GoogleOAuth = google_oauth.GoogleOAuth()

        userData = False

        # Fetch the access token
        for row in tokenQuery:
            userData = row
            refreshToken = row["refresh_token"]
            accessTokenData = GoogleOAuth.refresh(refreshToken)
            accessToken = accessTokenData.access_token

        # Calculate a datetime for the starting day of the week
        weekDateTime = datetime.strptime(str(startYear) + "-" + str(x) + "-" + "1", "%Y-%W-%w")
        week = x

        # Construct URL, remember to force mobile
        url = "https://www.lectio.dk/lectio/%s/SkemaNy.aspx?type=elev&elevid=%s&forcemobile=1&week=%i" %(userData["school_id"], userData["lectio_user_id"], int(str(week)+str(year)))

        # Download the schema from Lectio
        html = urllib2.urlopen(url).read()

        # Create a SoupStrainer scope to speed op parsing
        scope = SoupStrainer('a')

        # Initialize BeautifulSoup, the HTML parser
        soup = BeautifulSoup(html, parse_only=scope)

        # Find all the class hour elements in the HTML
        classHourElements = soup.findAll('a', attrs={'class': 's2skemabrik'})

        # Initialize array
        hourElements = []

        # Loop through all class hours elements
        for classHourElement in classHourElements:
            # Grab the title attribute containing all the information
            rawText = classHourElement['title']

            # Get the "main sections" separated by a double return \n\n
            mainSections = rawText.split("\n\n")

            # Grab the top section and split it by a single return \n
            topSection = mainSections[0].split("\n")

            # Initialize variables, assume that nothing is cancelled or changed
            isChangedOrCancelled = 0
            isCancelled = False
            isChanged = False

            # If the first item in the top section doesn't contain 'til',
            # it must be either cancelled or changed

            if not "til" in topSection[0]:
                isChangedOrCancelled = 1

                # If it says 'Aflyst!'
                if "Aflyst!" in topSection[0]:
                    # It must be cancelled
                    isCancelled = True
                else:
                    # Otherwise it must be changed
                    isChanged = True

            # Grab the date sections, fx: "15/5-2013 15:30 til 17:00"
            dateSections = topSection[0+isChangedOrCancelled].split(" ")

            # Grab the date, being the first (0) section
            date = dateSections[0]

            # Grab the start and end time, being the second (1) and fourth (3) section
            startTime = dateSections[1]
            endTime = dateSections[3]

            currentTimezone = timezone("Europe/Copenhagen")

            # Create a time object from the date and time information
            startDateTime = datetime.strptime("%s %s" % (date.strip(), startTime.strip()), "%d/%m-%Y %H:%M")
            endDateTime = datetime.strptime("%s %s" % (date.strip(), endTime.strip()), "%d/%m-%Y %H:%M")

            # Grab the group information
            #print topSection
            group = topSection[1+isChangedOrCancelled].strip("Hold: ").encode('utf-8')

            # Grab the teacher information
            teacher = topSection[2+isChangedOrCancelled].split(" ")[1]

            # Grab the room, and remove random info
            room = ""
            try:
                if not "rer:" in topSection[3 + isChangedOrCancelled]:
                    room = topSection[3 + isChangedOrCancelled].strip("Lokale: ").encode('utf-8').replace("r: ","")
            except IndexError:
                pass
            if not isCancelled:
                # Append the hour to the the hourElements array, in the format (Group, teacher, startDateTime, endDateTime, room)
                hourElements.append({
                    'group':            group,
                    'teacher':          teacher,
                    'startDateTime':    startDateTime,
                    'endDateTime':      endDateTime,
                    "room":             room
                })

        # A function to simplify the number of elements in the calendar, instead of having an element for each school hour, it creates one for the whole period
        def simplify (hourElements):
            startDates = [list(group) for k, group in itertools.groupby([d['startDateTime'] for d in hourElements], key=datetime.toordinal)]
            endDates = [list(group) for k, group in itertools.groupby([d['endDateTime'] for d in hourElements], key=datetime.toordinal)]
            days = []
            for i, dayStartDate in enumerate(startDates):
                days.append({
                    'group': 'School',
                    'teacher': '',
                    'startDateTime': startDates[i][0],
                    'endDateTime': endDates[i][-1],
                    'room': ''
                })
            return days

        # if simplify should be enabled
        doSimplify = int(task["simplify"])

        # Format: (Title, Description, StartDate, EndDate, Room)
        localCalendar = []

        # If simplify is enabled for this task, simplify
        if doSimplify:
            localCalendar = simplify(hourElements)
        else:
            for hourElement in hourElements:
                localCalendar.append(hourElement)

        # Assign the access token to the Google Calendar module
        GoogleCalendar = GoogleCalendarObject.GoogleCalendar()
        GoogleCalendar.access_token = accessToken

        # End day
        endDayString = datetime.strptime(weekDateTime.strftime("%Y") + ' ' + str(week-1) + ' 1', '%Y %W %w')
        endDayTimestamp = mktime(endDayString.timetuple())

        # Find the end day of the week
        endDayOfWeek = int(datetime.fromtimestamp(endDayTimestamp).strftime("%j"))+6

        # Fetch the events from the Google Calendar for the current week
        googleEvents = GoogleCalendar.events(task["calendar_id"], {
            "timeZone" : "Europe/Copenhagen",
            "timeMin" : datetime.fromtimestamp(mktime(timeLib.strptime(weekDateTime.strftime("%Y") + ' ' + str(week-1) + ' 1', '%Y %W %w'))).strftime('%Y-%m-%dT%H:%M:%SZ'),
            "timeMax" : datetime.fromtimestamp(mktime(timeLib.strptime(weekDateTime.strftime("%Y") + " " + str(endDayOfWeek), '%Y %j'))).strftime('%Y-%m-%dT%H:%M:%SZ')
        })

        # If the item attribute isn't found in the response, the Calendar doesn't exist, there for proceed to the next task
        if not "items" in googleEvents:
            continue

        # Sync local -> Google
        for localEvent in localCalendar:
            found = False

            # Loop through the Google events, and check if the local event exists, if not create it
            for googleEvent in googleEvents["items"]:
                if sameEvent(googleEvent,localEvent):
                    found = True

            # Create the event if it doesn't exist
            if found == False:
                GoogleCalendar.insertEvent(task["calendar_id"],{
                    "start" : {"timeZone" : "Europe/Copenhagen","dateTime" : localEvent["startDateTime"].strftime('%Y-%m-%dT%H:%M:%S.000')},
                    "end" : {"timeZone" : "Europe/Copenhagen","dateTime" : localEvent["endDateTime"].strftime('%Y-%m-%dT%H:%M:%S.000')},
                    "description" : createTitle(localEvent),
                    "summary" : createTitle(localEvent),
                })
            else:
                pass

        # Sync Google -> Local
        for googleEvent in googleEvents["items"]:
            found = False

            # Loop through the local events, to check if the Google event exists in the local calendar
            for localEvent in localCalendar:
                if sameEvent(googleEvent, localEvent):
                    found = True

            # If it doesn't, delete it from Google Calendar
            if not found:
                print "Delete"
                GoogleCalendar.deleteEvent(task["calendar_id"], googleEvent["id"])

        # Add Last updated timestamp
        session.execute('UPDATE tasks SET last_updated="%s" WHERE google_id="%s"' % (str(mktime(datetime.now().timetuple()))[:-2],userData["user_id"]))
        session.commit()

print "Done"