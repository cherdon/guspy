import os
import json
import logging
import datetime
from guspy.parsers import ShiftParser
import sys
try:
    objects = os.path.abspath(os.path.join(sys.prefix, 'resources', 'objects.json'))
    with open(objects, 'r') as infile:
        obj = json.load(infile)
except:
    objects = os.path.abspath(os.path.join(sys.prefix, 'local', 'resources', 'objects.json'))
    with open(objects, 'r') as infile:
        obj = json.load(infile)


def quote(string):
    return "'" + string + "'"


def bracket(string):
    return "(" + string + ")"


class CreateQuery:
    def __init__(self, obj_name):
        if obj_name in obj:
            self.obj = obj[obj_name]["Object"]

    def create(self, fields, filters, inclusive=True):
        try:
            query = "SELECT " + fields + \
                    " FROM " + self.obj + \
                    " WHERE ("
            for param in filters:
                if filters.index(param) == len(filters) - 1:
                    query += param + ")"
                else:
                    if inclusive:
                        query += param + " OR "
                    else:
                        query += param + " AND "
            return query
        except Exception as e:
            logging.error(e)


# Query the CaseId by the Case Number provided (single or a list), or simply CaseIds that are related to GRE
class Case:
    def __init__(self, case_number=None):
        self.case_number = case_number
        self.default = "Id"

    def from_single(self, fields=None):
        if not fields:
            fields = self.default
        case_details = CreateQuery("Case").create(fields=fields,
                                                  filters=[obj['Case']['CaseNumber'] + " = "
                                                           + quote(self.case_number)],
                                                  inclusive=True)
        return case_details

    def from_multiple(self, fields=None):
        if not fields:
            fields = self.default
        case_details = CreateQuery("Case").create(fields=fields,
                                                  filters=[obj['Case']['CaseNumber'] + " IN "
                                                           + self.case_number],
                                                  inclusive=True)
        return case_details

    def gre(self, fields=None):
        if not fields:
            fields = self.default
        case_details = CreateQuery("Case").create(fields=fields,
                                                  filters=[obj['Case']['Team'] + " = "
                                                           + quote("Release Management"),

                                                           obj['Case']['Team'] + " = "
                                                           + quote("Global Release Engineering")],
                                                  inclusive=True)
        return case_details


# Query the CaseComment based on CommentId, CaseId, or simply the CommentIds that are related to GRE
class CaseComment:
    def __init__(self, comment_id=None, case_number=None):
        self.comment_id = comment_id
        self.case_number = case_number
        self.default = "Id"

    def from_single(self, fields=None):
        if not fields:
            fields = self.default
        if self.comment_id:
            comment_details = CreateQuery("CaseComment").create(fields=fields,
                                                                filters=["Id = " + quote(self.comment_id)],
                                                                inclusive=True)
        else:
            cases = Case(self.case_number).from_single("Id")
            comment_details = CreateQuery("CaseComment").create(fields=fields,
                                                                filters=["ParentId IN " + bracket(cases)],
                                                                inclusive=True)
        return comment_details

    def from_multiple(self, fields=None):
        if not fields:
            fields = self.default
        if self.comment_id:
            comment_details = CreateQuery("CaseComment").create(fields=fields,
                                                                filters=["Id IN " + quote(self.comment_id)],
                                                                inclusive=True)
        else:
            cases = Case(self.case_number).from_multiple("Id")
            comment_details = CreateQuery("CaseComment").create(fields=fields,
                                                                filters=["ParentId IN " + bracket(cases)],
                                                                inclusive=True)
        return comment_details

    def gre(self, fields=None):
        if not fields:
            fields = self.default
        gre_case_ids = Case().gre("Id")
        comment_details = CreateQuery("CaseComment").create(fields=fields,
                                                            filters=["ParentId IN " + bracket(gre_case_ids)],
                                                            inclusive=True)
        return comment_details


# Query ScrumTeamMember attributes based on Team Name, or simply the Member Names in GRE
class ScrumMember:
    def __init__(self, team_name=None):
        self.team_name = team_name
        self.default = obj['ScrumMember']["MemberName"]

    def from_single(self, fields=None):
        if not fields:
            fields = self.default
        team_members = CreateQuery("ScrumMember").create(fields=fields,
                                                         filters=[obj['ScrumMember']['TeamName'] + " = "
                                                                  + quote(self.team_name)],
                                                         inclusive=True)
        return team_members

    def gre(self, fields=None):
        if not fields:
            fields = self.default
        team_members = CreateQuery("ScrumMember").create(fields=fields,
                                                         filters=[obj['ScrumMember']['TeamName'] + " = "
                                                                  + quote('Global Release Engineering')],
                                                         inclusive=True)
        return team_members


# Query the attributes of the User based on their individual UserIds
class User:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.default = "Name"

    def get_single(self, fields=None):
        if not fields:
            fields = self.default
        users = CreateQuery("User").create(fields=fields,
                                           filters=["Id = " + quote(self.user_id)],
                                           inclusive=True)
        return users

    def get_multiple(self, fields=None):
        if not fields:
            fields = self.default
        users = CreateQuery("User").create(fields=fields,
                                           filters=["Id IN " + bracket(self.user_id)],
                                           inclusive=True)
        return users

    def gre(self, fields=None):
        if not fields:
            fields = self.default
        team = ScrumMember().gre()
        users = CreateQuery("User").create(fields=fields,
                                           filters=["Id IN " + bracket(team)],
                                           inclusive=True)
        return users


class ReleaseEvent:                    # TODO LOGGING exception for no case_id
    def __init__(self, case_id=None):
        self.case_id = case_id
        self.default = obj['ReleaseEvent']['Case']

    def from_single(self, fields=None, date=None, shift="SIN"):
        release_event_details = None
        if not fields:
            fields = self.default
        if date:
            shift_start, shift_end = self.initial_date(date=date, shift=shift.upper())
            if shift_start:
                release_event_details = CreateQuery("ReleaseEvent").create(fields=fields,
                                                                           filters=[obj['ReleaseEvent']['Case'] + " = "
                                                                                    + quote(self.case_id),
                                                                                    obj['ReleaseEvent']['Start'] + " < "
                                                                                    + shift_end,
                                                                                    obj['ReleaseEvent']['End'] + " > "
                                                                                    + shift_start],
                                                                           inclusive=False)
        else:
            release_event_details = CreateQuery("ReleaseEvent").create(fields=fields,
                                                                       filters=[obj['ReleaseEvent']['Case'] + " = "
                                                                                + quote(self.case_id)],
                                                                       inclusive=True)
        return release_event_details

    def from_multiple(self, fields=None):
        if not fields:
            fields = self.default
        release_event_details = CreateQuery("ReleaseEvent").create(fields=fields,
                                                                   filters=[obj['ReleaseEvent']['Case'] + " IN "
                                                                            + bracket(self.case_id)],
                                                                   inclusive=True)
        return release_event_details

    def initial_date(self, date, shift):
        if not date:
            date = datetime.datetime.utcnow()
        else:
            date = datetime.datetime.strptime(date, "%Y-%m-%d")
        shift_start, shift_end = ShiftParser(date, shift).get_shifts()
        return shift_start, shift_end

    def gre(self, fields=None, date=None, shift="SIN"):
        if not fields:
            fields = self.default
        cases = Case().gre("Id")
        shift_start, shift_end = self.initial_date(date=date, shift=shift)
        if shift_start:
            release_event_details = CreateQuery("ReleaseEvent").create(fields=fields,
                                                                       filters=[obj['ReleaseEvent']['Case'] + " IN "
                                                                                + bracket(cases),
                                                                                obj['ReleaseEvent']['Start'] + " < "
                                                                                + shift_end,
                                                                                obj['ReleaseEvent']['End'] + " > "
                                                                                + shift_start],
                                                                       inclusive=False)
        else:
            release_event_details = None
        return release_event_details


class Task:
    def __init__(self, case_id=None):
        self.case_id = case_id
        self.default = "Subject"

    def from_single(self, fields=None):
        if not fields:
            fields = self.default
        task_details = CreateQuery("Task").create(fields=fields,
                                                  filters=[obj['Task']['Case'] + " = " + quote(self.case_id)],
                                                  inclusive=True)
        return task_details

    def from_multiple(self, fields=None):
        if not fields:
            fields = self.default
        task_details = CreateQuery("Task").create(fields=fields,
                                                  filters=[obj['Task']['Case'] + " IN " + bracket(self.case_id)],
                                                  inclusive=True)
        return task_details

    def gre(self, fields=None):
        if not fields:
            fields = self.default
        cases = Case().gre("Id")
        task_details = CreateQuery("Task").create(fields=fields,
                                                  filters=[obj['Task']['Case'] + " IN " + bracket(cases)],
                                                  inclusive=True)
        return task_details


class InstanceDatacenter:
    def __init__(self):
        self.default = "Pod_Name__c"

    def gre(self, fields=None):
        if not fields:
            fields = self.default
        instance_details = CreateQuery("InstanceDatacenter").create(fields=fields,
                                                                    filters=[obj['InstanceDatacenter']['Lifecycle'] + " LIKE " + quote("%Go Live%")],
                                                                    inclusive=True)
        return instance_details


# if __name__ == "__main__":
    # inst = InstanceDatacenter().gre("Super_Pod__c, Pod_Name__c, Status__c")
    # print(inst)
#     from guspy.access import Gus
#     config = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, 'resources', 'config.json'))
#     with open(config, 'r') as passfile:
#         passes = json.load(passfile)
#
#     instance = Gus(username=passes['username'],
#                    password=passes['password'])
#     conn = instance.connect()
    # soql = SOQLQuery(connection=conn)
#
#     queries = CaseComment().gre("CreatedBy.Name, CreatedDate, CommentBody, CreatedBy.Id")
#    queries += " LIMIT 200"
#     print(queries)
    # soql = SOQLQuery(connection=conn)
#
    # queries = CaseComment().gre("CreatedBy.Name, CreatedDate, CommentBody, CreatedBy.Id")
#     queries += " LIMIT 200"
#     print(queries)
#     queries = ReleaseEvent().gre(fields="Name, Id, Release_Name__c, Scheduled_Start__c,"
#                                         " Scheduled_End__c, Deployment_Instances__c, ChangeCase__c",
#                                  date="2019-06-09",
#                                  shift="DUB")
#     print(queries)
#
#     queries = Task().gre(fields="Subject, Status, WhatId")
#                                  date=None,
#                                  shift="SIN")
#
#     queries = Task().gre(fields="Subject, Status, WhatId")
#     print(queries)
#     res = soql.release_events(queries)
#     for index, row in res.iterrows():
#         print(row)