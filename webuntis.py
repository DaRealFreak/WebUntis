# coding=utf-8
import argparse
import collections
import cookielib
import datetime
import gzip
import json
import time
import urllib
import urllib2
from StringIO import StringIO

SCHOOL_NAME = 'IT-Schule Stuttgart'
# taken from html sourcecode of the page after successful login
CLASS_ID = 281
LICENSE_KEY = '"licence":{"name":"IT-Schule Stuttgart","name2":"D-70565, Breitwiesenstr. 20-22"}'


class WebUntis(object):
    AUTHENTICATION_URL = 'https://mese.webuntis.com/WebUntis/j_spring_security_check'
    SCHEDULE_DATA_URL = 'https://mese.webuntis.com/WebUntis/api/public/timetable/weekly/data?elementType=1&elementId' \
                        '=%s&date=%s&formatId=1'
    SCHEDULE_INFO_URL = 'https://mese.webuntis.com/WebUntis/api/public/lesson/info?date=%d&starttime=%d&endtime=%d' \
                        '&elemid=%d&elemtype=1&ttFmtId=1 '

    @staticmethod
    def handle_response(response):
        """
        check for gzip encoding and decode if found

        :param response:
        :return:
        """
        if response.info().get('Content-Encoding') == 'gzip':
            buf = StringIO(response.read())
            f = gzip.GzipFile(fileobj=buf)
            _data = f.read()
        else:
            _data = response.read()
        return _data

    @staticmethod
    def multikeysort(items, columns):
        """
        sort function with primary and secondary order

        :param items:
        :param columns:
        :return:
        """
        from operator import itemgetter
        comparers = [((itemgetter(col[1:].strip()), -1) if col.startswith('-') else
                      (itemgetter(col.strip()), 1)) for col in columns]

        def comparer(left, right):
            for fn, mult in comparers:
                result = cmp(fn(left), fn(right))
                if result:
                    return mult * result
            else:
                return 0

        return sorted(items, cmp=comparer)

    @staticmethod
    def parse_schedule(schedule):
        """
        parse the schedule json block

        :param schedule:
        :return:
        """
        tmp_schedule = []
        periods = schedule['data']['result']['data']['elementPeriods'][str(CLASS_ID)]
        for i in range(0, len(periods), 2):
            # 2 steps for double periods
            period = periods[i]
            tmp_schedule.append({
                "date": period['date'],
                "starttime": period['startTime'],
                "endtime": period['endTime']
            })
        return WebUntis.multikeysort(tmp_schedule, ['date', 'starttime'])

    @staticmethod
    def parse_lesson(_data):
        """
        parse the lesson json block

        :param _data:
        :return:
        """
        _data = _data['data']
        lesson_data = {'date': datetime.datetime.strptime(str(_data['date']), '%Y%m%d').strftime('%Y-%m-%d')}
        blocks = _data['blocks']
        # array in array? what is the second one for?
        for _block in blocks:
            for block in _block:
                if block['lessonTopic']:
                    lesson_data['subject'] = block['subjectName']
                    lesson_data['teacher'] = block['teacherNameLong']
                    lesson_data['topic'] = block['lessonTopic']['text']
        return lesson_data

    @staticmethod
    def parse_date(_dt):
        """
        get the day formats for the script and output

        :param _dt: datetime of current week day
        :return:
        """
        _start = _dt - datetime.timedelta(days=_dt.weekday())
        return _start.strftime('%Y-%m-%d')

    @staticmethod
    def prepare_urllib2():
        """
        add cookiejar and cookieprocessor to urllib2 module

        :return:
        """
        cj = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

        # Chrome Version 61.0.3163.100 (Official Build) (64-bit)
        opener.addheaders = [
            ('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/61.0.3163.100 Safari/537.36'),
            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'),
            ('Accept-Encoding', 'gzip, deflate, br'),
            ('Accept-Language', 'en-DE,en-US;q=0.8,en;q=0.6'),
            ('Connection', 'keep-alive')
        ]

        urllib2.install_opener(opener)

    @staticmethod
    def pretty_print(summary):
        """
        pretty print for copypasta

        :param summary:
        :return:
        """
        for week, lessons in summary.iteritems():
            week_start_timestamp = datetime.datetime.fromtimestamp(float(week))
            week_end_timestamp = week_start_timestamp + datetime.timedelta(days=5)
            week_start = week_start_timestamp.strftime('%d-%m-%Y')
            week_end = week_end_timestamp.strftime('%d-%m-%Y')
            print "\nUnterricht von: %s - %s" % (week_start, week_end)
            for lesson in lessons:
                if all(k in lesson for k in ('subject', 'teacher', 'topic')):
                    print "%s (%s): %s" % (lesson['subject'], lesson['teacher'], lesson['topic'].replace('\n', ', '))

    def __init__(self):
        """
        initializing function
        """
        self.prepare_urllib2()
        self.login()
        summary = self.extract_schedule()

        self.pretty_print(summary)

    def login(self):
        """
        login to webuntis

        :return:
        """
        payload = {
            'school': SCHOOL_NAME,
            'j_username': args.username,
            'j_password': args.password,
            'token': ''
        }

        data = urllib.urlencode(payload)
        req = urllib2.Request(self.AUTHENTICATION_URL, data)
        resp = urllib2.urlopen(req)
        data = self.handle_response(resp)

        if LICENSE_KEY in data:
            print "login successful"
        else:
            print "login not successful"
            exit()

    def extract_schedule(self):
        """
        extract the schedule from startdate to enddate

        :return:
        """
        if args.startdate:
            startdate_str = self.parse_date(datetime.datetime.strptime(args.startdate, '%d-%m-%Y'))
            startdate = datetime.datetime.strptime(startdate_str, '%Y-%m-%d')
        else:
            startdate = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

        if args.enddate:
            dt = datetime.datetime.strptime(args.enddate, '%d-%m-%Y')
        else:
            dt = datetime.datetime.today()
        start = datetime.datetime(*dt.timetuple()[:6])

        summary = {}
        while startdate < start:
            parsed_day = self.parse_date(startdate)
            data_url = self.SCHEDULE_DATA_URL % (CLASS_ID, parsed_day)
            req = urllib2.Request(data_url)
            resp = urllib2.urlopen(req)
            data = self.handle_response(resp)

            weekly_schedule = self.parse_schedule(json.loads(data))
            weekly_lessons = []

            for element in weekly_schedule:
                info_url = self.SCHEDULE_INFO_URL % (element['date'], element['starttime'], element['endtime'],
                                                     CLASS_ID)
                req = urllib2.Request(info_url)
                resp = urllib2.urlopen(req)
                data = self.handle_response(resp)
                lesson = self.parse_lesson(json.loads(data))
                lesson['starttime'] = element['starttime']
                lesson['endtime'] = element['endtime']
                weekly_lessons.append(lesson)

            # sort
            weekly_lessons = self.multikeysort(weekly_lessons, ['date', 'starttime'])
            summary["%d" % time.mktime(startdate.timetuple())] = weekly_lessons

            # increase startdate
            startdate = startdate + datetime.timedelta(weeks=1)

        # return sorted summary by timestamp
        # noinspection PyArgumentList
        return collections.OrderedDict(sorted(summary.items()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', help='its username', required=True)
    parser.add_argument('-p', '--password', help='its password', required=True)
    parser.add_argument('-s', '--startdate', help='start date in d-m-Y format')
    parser.add_argument('-e', '--enddate', help='end date in d-m-Y format')
    args = parser.parse_args()
    WebUntis()
