import datetime
import json
import os
import smtplib
import time
from urllib2 import urlopen
from twilio.rest import Client

def park():
    parkingUrl = urlopen('https://api.parkwhiz.com/v4/venues/448854/events/?fields=%3Adefault%2Csite_url%2Cavailability%2Cvenue%3Atimezone&q=%20starting_after%3A2021-01-17T00%3A00%3A00-07%3A00&sort=start_time&zoom=pw%3Avenue')
    data = parkingUrl.read()
    scrape = json.loads(data)
    now = datetime.datetime.now()
    endDate = now + datetime.timedelta(days=30)

    availableDates = []
    for row in scrape:
        startDate, startTime = row['start_time'].split('T')
        date = datetime.datetime.strptime(startDate,'%Y-%m-%d')
        if '12:30' in startTime:
            # only want 7am slots
            continue
        if date < now:
            # only want dates in future
            continue
        if date > endDate:
            # only checking 1mo ahead
            break
        if date.weekday() < 5:
            # only want weekends
            continue
        availability = row['availability']['available']
        if availability != 0:
            availableDates.append(date.strftime('%m/%d'))

    dates = set(availableDates)
    blacklist = set(['02/21']) # add dates you already booked here
    availableDates = list(dates.difference(blacklist))
    if len(availableDates) > 0 :
        sendText(availableDates)

def sendText(dates):
    delimiter = 'DELIMITER'
    with open('sent.txt', 'r') as f:
        lastLine = f.readlines()[-1]
    line = lastLine.split(delimiter)
    time = datetime.datetime.strptime(line[0], "%m/%d/%Y,%H:%M:%S")
    prevDates = eval(line[1])
    minsDifference = (datetime.datetime.now() - time).seconds / 60

    # send text if dates are different from last sent text OR
    # it's been over an hour since the last text
    if (prevDates != dates or minsDifference > 60):
        message = "Copper Parking Available on " + ','.join(dates)
        # fill with data fron https://www.twilio.com/console
        client = Client('ACCOUNT_SID', 'ACCOUNT_AUTH')
        message = client.messages \
                    .create(
                        body=message,
                        from_='YOUR_TWILIO_NUMBER',
                        to='YOUR_NUMBER'
               )
        write('sent.txt' , getNow() + delimiter + str(dates))

def write(filename, data):
    if os.path.isfile(filename):
        with open(filename, 'a') as f:
            f.write('\n' + data)
    else:
        with open(filename, 'w') as f:
            f.write(data)

def getNow():
    now = datetime.datetime.now()
    return now.strftime("%m/%d/%Y,%H:%M:%S")

park()
write('runs.txt' , "Ran at: " + getNow())
