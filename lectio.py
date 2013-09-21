import urllib2
import time
from time import mktime
from datetime import datetime
import urllib
import sqlalchemy
from dateutil import parser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from googleauth import google_oauth
import config
import calendar
from googlecalendar import calendar as GoogleCalendar
import itertools
from bs4 import BeautifulSoup, SoupStrainer

__author__ = 'frederik'

# Crete the database Engine
engine = create_engine(config.database+'://'+config.db_user+':'+config.db_password+'@'+config.db_host+'/'+config.db_database)

Session = sessionmaker(bind=engine)

# create a Session
session = Session()

# Create the tasks table, if it doesn't exist
session.execute("CREATE TABLE IF NOT EXISTS `tasks` ( `id` int(11) NOT NULL AUTO_INCREMENT, `calendar_id` varchar(80) DEFAULT NULL, `google_id` varchar(80) DEFAULT NULL, `lectio_id` varchar(80) DEFAULT NULL, `school_id` varchar(45) DEFAULT NULL, PRIMARY KEY (`id`)) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=latin1")

tasks = session.execute("SELECT * FROM tasks")
for task in tasks:
    # Construct URL, remember to force mobile
    url = "https://www.lectio.dk/lectio/%s/SkemaNy.aspx?type=elev&elevid=%s&forcemobile=1&week=%i" %(task["school_id"], task["lectio_id"], 382013)

    print("Downloading from Lectio...")
    # Download the schema from Lectio
    html = urllib2.urlopen(url).read()

    # Create a SoupStrainer scope to speed op parsing
    scope = SoupStrainer('a')

    print("Initializing HTML parser...")
    # Initializee BeautifulSoupt, the HTML parser
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

        # Create a time object from the date and time information
        startDateTime = parser.parse("%s %s CEST" % (date, startTime))
        endDateTime = parser.parse("%s %s CEST" % (date, endTime))

        # Grab the group information
        #print topSection
        group = topSection[1+isChangedOrCancelled].strip("Hold: ").encode('utf-8')

        # Grab the teacher information
        teacher = topSection[2+isChangedOrCancelled].split(" ")[1]

        # Grab the room, and remove random info
        if not "rer:" in topSection[3+isChangedOrCancelled]:
            room = topSection[3+isChangedOrCancelled].strip("Lokale: ").encode('utf-8').replace("r: ","")

        #datetime.fromtimestamp(mktime(startDateTime))
        #datetime.fromtimestamp(mktime(endDateTime))

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
            localCalendar.append((hourElement['group'], "", hourElement['startDateTime'], hourElement['endDateTime'], hourElement['room']))
    print(localCalendar)

    tokenQuery = session.execute('SELECT * FROM user WHERE user_id="'+task["google_id"]+'"')

    GoogleOAuth = google_oauth.GoogleOAuth()

    for row in tokenQuery:
        refreshToken = row["refresh_token"]
        accessTokenData = GoogleOAuth.refresh(refreshToken)
        accessToken = accessTokenData.access_token

    GoogleCalendar = GoogleCalendar.GoogleCalendar()
    GoogleCalendar.access_token = accessToken

    googleEvents = GoogleCalendar.events(task["calendar_id"])

    for localEvent in localCalendar:
        found = False

        for googleEvent in googleEvent["items"]:
            if calendar.timegm(googleEvent["start"]["datetime"].utctimetuple()) == calendar.timegm(localEvent["startDateTime"].utctimetuple()):
                found = True


