# WebUntis

small script to scrap the school diary entries from [WebUntis](https://mese.webuntis.com/WebUntis)


### Installing
This script runs with [Python 3](https://www.python.org).
There is a currently working [Python 2 branch](https://github.com/DaRealFreak/WebUntis/tree/Python-2.7), but I'm not going to update it anymore.

### Dependencies
 - none

### Setting up your settings.json
The school name and class id have to get changed manually in the settings.json since I can't know the school name and don't want to interpret/execute javascript in Python and WebUntis isn't even working without Javascript(hooray to the public service implementations *cough*)

The school name should be given to you by your school.
The class id can be extracted from the traffic (open the network tab and look for XHR requests like ```data?elementType=1&elementId=281&date=2018-02-19```. The elementId is your class id)

### Usage
It is recommended to run WebUntis only from the command line
```
python usage.py --username "your_username" --password "your_password" [--startdate "01-01-2018"] [--enddate "15-01-2018"]
```
if no start date or end date is passed to the script it'll use the current week by default

## Development
Want to contribute? Great!

I'm always glad hearing about bugs or pull requests.


## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
