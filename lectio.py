import urllib2
import time
from time import mktime
from datetime import datetime
from dateutil import parser
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
import time

__author__ = 'frederik'

def createTitle (localEvent):
    return localEvent["group"] + " - " + localEvent["teacher"] + " - " + localEvent["room"]

def sameEvent (googleEvent, localEvent):
    startTuple = datetime.utctimetuple(localEvent["startDateTime"])
    endTuple = datetime.utctimetuple(localEvent["endDateTime"])
    return (calendar.timegm(parser.parse(googleEvent["start"]["dateTime"]).utctimetuple()) == calendar.timegm(startTuple) and calendar.timegm(parser.parse(googleEvent["end"]["dateTime"]).utctimetuple()) == calendar.timegm(endTuple) and googleEvent["summary"] == createTitle(localEvent))

# Crete the database Engine
engine = create_engine(config.database+'://'+config.db_user+':'+config.db_password+'@'+config.db_host+'/'+config.db_database)

Session = sessionmaker(bind=engine)

# create a Session
session = Session()

# Create the tasks table, if it doesn't exist
session.execute("CREATE TABLE IF NOT EXISTS `tasks` ( `id` int(11) NOT NULL AUTO_INCREMENT, `calendar_id` varchar(255) DEFAULT NULL, `google_id` varchar(80) DEFAULT NULL, `lectio_id` varchar(80) DEFAULT NULL, `school_id` varchar(45) DEFAULT NULL, PRIMARY KEY (`id`)) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=latin1")

tasks = session.execute("SELECT * FROM tasks")

currentWeekDateTime = datetime.date(datetime.now(timezone('Europe/Copenhagen')))
currentWeek = int(currentWeekDateTime.strftime("%U"))
endWeek = currentWeek+4
yearChange = False
startYear = int(currentWeekDateTime.strftime("%Y"))

if currentWeek+4 > 53:
    endWeek = 1 + (currentWeek+4-53)
    yearChange = True

for task in tasks:
    for x in range(currentWeek, endWeek):
        weekDateTime = datetime.date(datetime.now(timezone('Europe/Copenhagen')))
        week =  int(weekDateTime.strftime("%U"))
        if x < currentWeek:
            year = startYear+1
        else:
            year = startYear

        # Construct URL, remember to force mobile
        url = "https://www.lectio.dk/lectio/%s/SkemaNy.aspx?type=elev&elevid=%s&forcemobile=1&week=%i" %(task["school_id"], task["lectio_id"], int(str(week)+str(year)))

        print("Downloading from Lectio...")
        # Download the schema from Lectio
        html = urllib2.urlopen(url).read()

        # Create a SoupStrainer scope to speed op parsing
        scope = SoupStrainer('a')

        print("Initializing HTML parser...")
        # Initializee BeautifulSoup, the HTML parser
        soup = BeautifulSoup(html, parse_only=scope)

        print("Parsing HTML...")
        # Find all the class hour elements in the HTML
        classHourElements = soup.findAll('a', attrs={'class': 's2skemabrik'})

        # Initialize array
        hourElements = []

        # Loop through all class hours elements
        for classHourElement in classHourElements:
            # Grab the title attribute containing all the information
            rawText = classHourElement['title']

            # Get the "main sections" seperated by a double return \n\n
            mainSections = rawText.split("\n\n")

            # Grab the top section and split it by a single return \n
            topSection = mainSections[0].split("\n")

            # Initialize variables, assume that nothing is cancelled or changed
            isChangedOrCancelled = 0
            isCancelled = False
            isChanged = False

            # If the first item in the top section doesn't contain 'til',
            # it must be either cancelled or changed
            if (not "til" in topSection[0]):
                isChangedOrCancelled = 1

                # If it says 'Aflyst!'
                if (topSection[0] == "Aflyst!"):
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
            startDateTime = parser.parse("%s %s CEST" % (date, startTime))
            endDateTime = parser.parse("%s %s CEST" % (date, endTime))

            # Grab the group information
            #print topSection
            group = topSection[1+isChangedOrCancelled].strip("Hold: ").encode('utf-8')

            # Grab the teacher information
            teacher = topSection[2+isChangedOrCancelled].split(" ")[1]

            # Grab the room, and remove random info
            room = ""
            try:
                if not "rer:" in topSection[3+isChangedOrCancelled]:
                    room = topSection[3+isChangedOrCancelled].strip("Lokale: ").encode('utf-8').replace("r: ","")
            except IndexError:
                pass

            hourElements.append({
                'group':            group,
                'teacher':          teacher,
                'startDateTime':    startDateTime,
                'endDateTime':      endDateTime,
                "room":             room
            })

        #print(hourElements)

        def simplify (hourElements):
            startDates = [list(group) for k, group in itertools.groupby([datetime.fromtimestamp(mktime(d['startDateTime'])) for d in hourElements], key=datetime.toordinal)]
            endDates = [list(group) for k, group in itertools.groupby([datetime.fromtimestamp(mktime(d['endDateTime'])) for d in hourElements], key=datetime.toordinal)]
            #print(startDates)
            days = []
            for i, dayStartDate in enumerate(startDates):
                days.append(("School", "", startDates[i][0], endDates[i][-1]))
            return days

        doSimplify = 0
        # Format: (Title, Description, StartDate, EndDate, Room)
        localCalendar = []

        if doSimplify:
            localCalendar = simplify(hourElements)
        else:
            for hourElement in hourElements:
                localCalendar.append(hourElement)

        tokenQuery = session.execute('SELECT * FROM user WHERE user_id="'+task["google_id"]+'"')

        GoogleOAuth = google_oauth.GoogleOAuth()

        for row in tokenQuery:
            refreshToken = row["refresh_token"]
            accessTokenData = GoogleOAuth.refresh(refreshToken)
            accessToken = accessTokenData.access_token

        GoogleCalendar = GoogleCalendarObject.GoogleCalendar()
        GoogleCalendar.access_token = accessToken

        endDayOfWeek = int(datetime.fromtimestamp(mktime(time.strptime(weekDateTime.strftime("%Y") + ' ' + str(week-1) + ' 1', '%Y %W %w'))).strftime("%j"))+6

        googleEvents = GoogleCalendar.events(task["calendar_id"], {
            "timeZone" : "0200",
            "timeMin" : datetime.fromtimestamp(mktime(time.strptime(weekDateTime.strftime("%Y") + ' ' + str(week-1) + ' 1', '%Y %W %w'))).strftime('%Y-%m-%dT%H:%M:%S.000-0200'),
            "timeMax" : datetime.fromtimestamp(mktime(time.strptime(weekDateTime.strftime("%Y") + " "+ str(endDayOfWeek), '%Y %j'))).strftime('%Y-%m-%dT%H:%M:%S.000-0200')
        })

        print task["calendar_id"]
        print GoogleCalendar.access_token
        print googleEvents
        print row["refresh_token"]

        if not "items" in googleEvents:
            continue

        # Sync local -> Google
        for localEvent in localCalendar:
            found = False

            for googleEvent in googleEvents["items"]:
                if sameEvent(googleEvent,localEvent):
                    found = True

            if found == False:
                timeZone = localEvent["startDateTime"].strftime("%z")
                if timeZone == "":
                    timeZone = "0000"
                GoogleCalendar.insertEvent(task["calendar_id"],{
                    "start" : {"dateTime" : localEvent["startDateTime"].strftime('%Y-%m-%dT%H:%M:%S.000-')+timeZone},
                    "end" : {"dateTime" : localEvent["endDateTime"].strftime('%Y-%m-%dT%H:%M:%S.000-')+timeZone},
                    "description" : createTitle(localEvent),
                    "summary" : createTitle(localEvent)
                })


        # Sync Google -> Local
        for googleEvent in googleEvents["items"]:
            found = False
            for localEvent in localCalendar:
                if sameEvent(googleEvent, localEvent):
                    found = True

            if found == False:
                GoogleCalendar.deleteEvent(task["calendar_id"], googleEvent["id"])