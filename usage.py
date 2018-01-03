#!/usr/bin/python
# -*- coding: utf-8 -*-
import argparse

from webuntis import WebUntis

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', help='its username', required=True)
    parser.add_argument('-p', '--password', help='its password', required=True)
    parser.add_argument('-s', '--startdate', help='start date in d-m-Y format', default='')
    parser.add_argument('-e', '--enddate', help='end date in d-m-Y format', default='')
    args = parser.parse_args()

    webuntis = WebUntis(username=args.username, password=args.password)
    result_summary = webuntis.extract_schedule(start_date=args.startdate, end_date=args.enddate)
    WebUntis.pretty_print(result_summary)
