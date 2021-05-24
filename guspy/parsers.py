import os
import json
from datetime import datetime, timedelta
import sys
try:
    cli = os.path.abspath(os.path.join(sys.prefix, 'local', 'resources', 'cli.json'))
    with open(cli, 'r') as infile:
        cli = json.load(infile)
except:
    cli = os.path.abspath(os.path.join(sys.prefix, 'resources', 'cli.json'))
    with open(cli, 'r') as infile:
        cli = json.load(infile)


def last_item(ls, item):
    return ls.index(item) == (len(ls) - 1)


class DateTimeParser:
    def __init__(self, date_time, format="common"):
        self.date_time = date_time
        self.format = format

    def convert(self, format="common"):
        try:
            if format == "SF":
                dt = datetime.strptime(self.date_time, "%Y-%m-%d %H:%M:%S")
            elif format == "SOQL":
                dt = datetime.strptime(self.date_time, "%Y-%m-%dT%H:%M:%S.%f%z")
            else:
                dt = datetime.strptime(self.date_time, "%Y-%m-%d")
        except:
            dt = self.date_time
        return dt

    def sf_standard(self):
        dt = self.convert(self.format)
        dt = dt.strftime("%Y-%m-%d %H:%M:%S")
        return dt

    def soql_standard(self):
        dt = self.convert(self.format)
        dt = dt.strftime("%Y-%m-%dT%H:%M:%S.%f%z") + "Z"
        return dt

    def easy_view_standard(self):
        dt = self.convert(self.format)
        dt = dt.strftime("%d %b, %I:%M%p")
        return dt

    def hour(self):
        dt = self.convert(self.format)
        hour = dt.hour
        return hour

    def day(self):
        dt = self.convert(self.format)
        day = dt.weekday()
        return day

    def weekday(self):
        if self.day() < 5:
            return True
        else:
            return False


class CaseCommentParser:
    def __init__(self, comment):
        self.comment = comment
        self.items = self.comment.split()

    def search(self, word):
        try:
            inx = self.items.index(word)
            var = self.items[inx+1]
        except:
            var = None
        return var

    def check(self, value):
        if value and value[0] == "-":
            return None
        else:
            return value

    def split(self):
        parsed = dict()
        for key, value in cli.items():
            for command in value:
                result = self.check(self.search(command))
                if result:
                    parsed[key] = result
                    break
                elif not result and last_item(value, command):
                    parsed[key] = None
        parsed = self.format(parsed)
        return parsed

    def format(self, parsed_dict):
        if parsed_dict.get("Version"):
            parsed_dict['Version'] = self.version_format(parsed_dict['Version'])
        if parsed_dict.get("Chatter"):
            parsed_dict['Chatter'] = self.chatter_format(parsed_dict['Chatter'])
        return parsed_dict

    def version_format(self, version):
        try:
            version = version.split("@")[1]
            try:
                version = version.split(",")[0]
            except:
                pass
        except:
            pass
        return version

    def chatter_format(self, chatter_str):
        return chatter_str.strip('"')


class ShiftParser:
    def __init__(self, date_time, shift):
        self.date_time = DateTimeParser(date_time)
        self.shift = shift

    def get_timing(self):
        start, end = None, None
        if self.date_time.weekday():
            if self.shift == "SIN":
                start = (1, 0)
                end = (9, 0)
            elif self.shift == "DUB":
                start = (9, 0)
                end = (16, 0)
            elif self.shift == "USA":
                start = (16, 0)
                end = (1, 0)
            elif self.shift == "ALL":
                start = (1, 0)
                end = (1, 0)
        else:
            if self.shift == "SIN":
                start = (1, 0)
                end = (13, 0)
            elif self.shift == "USA":
                start = (13, 0)
                end = (1, 0)
            elif self.shift == "ALL":
                start = (1, 0)
                end = (1, 0)
        return start, end

    def get_shifts(self):
        start, end = self.get_timing()
        date_time = self.date_time.convert()
        if not start:
            shift_start, shift_end = start, end
        else:
            if start[0] < end[0]:       # normal operations
                shift_start = date_time.replace(hour=start[0], minute=start[1], second=0, microsecond=0)
                shift_end = date_time.replace(hour=end[0], minute=end[1], second=0, microsecond=0)
            else:                         # overnight
                shift_start = date_time.replace(hour=start[0], minute=start[1], second=0, microsecond=0)
                shift_end = date_time.replace(hour=end[0], minute=end[1], second=0, microsecond=0) \
                            + timedelta(days=1)
            shift_start = DateTimeParser(shift_start).soql_standard()
            shift_end = DateTimeParser(shift_end).soql_standard()
        return shift_start, shift_end