import os
import json
import logging
import datetime
from guspy.parsers import ShiftParser
from guspy.filters import *
import sys
try:
    objects = os.path.abspath(os.path.join(sys.prefix, 'resources', 'objects.json'))
    with open(objects, 'r') as infile:
        obj = json.load(infile)
except:
    try:
        objects = os.path.abspath(os.path.join(sys.prefix, 'local', 'resources', 'objects.json'))
        with open(objects, 'r') as infile:
            obj = json.load(infile)
    except:
        obj = os.path.abspath(os.path.join(sys.prefix, os.path.pardir, 'resources', 'objects.json'))
        with open(obj, 'r') as infile:
            obj = json.load(infile)

# TODO deprecate this in v2.0
# def quote(string):
#     return "'" + string + "'"
#
#
# def bracket(string):
#     return "(" + string + ")"


class Query:
    def __init__(self, obj_name):
        if obj_name in obj:
            self.obj = obj[obj_name]["Object"]
        else:
            logging.warning(f"[Query] Warning: {obj_name} is not found in our compilation. ")
            self.obj = obj_name

    def create(self, fields, filters=None, sort_by=None, sort_seq=None, limit=None):
        try:
            query = f"SELECT {fields} FROM {self.obj}"
            if filters:
                query += f" WHERE {filters}"
            if sort_by and sort_seq:
                query += f" ORDER BY {sort_by} {sort_seq}"
            if limit:
                query += f" LIMIT {limit}"
            return query
        except Exception as e:
            print(f"[Query Creation] Unable to create query: {e}")


# Query the CaseId by the Case Number provided (single or a list), or simply CaseIds that are related to GRE
class GUSObject:
    def __init__(self, fields=None, filters=None, limit=None, sort_by=None, sort_seq=None):
        self.field_value = "Id"
        self.fields(fields)
        self.filters(filters)
        self.limit(limit)
        self.sort(sort_by, sort_seq)

    def fields(self, fields):
        if type(fields) == str:
            self.field_value = fields
        elif type(fields) == list:
            self.field_value = ",".join(fields)
        else:
            raise TypeError(f"[Case] Fields specified must be 'str' or 'list' type, not {str(type(fields))}")

    def filters(self, filters, inclusive=True):
        if self.filter_value:
            self.filter_value = f" {'AND' if inclusive else 'OR'} {filters}"
        else:
            self.filter_value = filters

    def limit(self, num=15):
        self.limit_value = num

    def sort(self, field, seq="DESC"):
        self.sort_by = field
        self.sort_seq = seq

    def query_object(self, object_name):
        self.query_obj = Query(object_name)

    def generate(self):
        self.query = self.query_obj.create(
            fields=self.field_value,
            filters=self.filter_value,
            sort_by=self.sort_by,
            sort_seq=self.sort_seq,
            limit=self.limit_value
        )
        return self.query


# Query the CaseId by the Case Number provided (single or a list), or simply CaseIds that are related to GRE
class Apprise(GUSObject):
    def create(self):
        self.query_object("AppriseLogs")
        return self.generate()


# Query the CaseId by the Case Number provided (single or a list), or simply CaseIds that are related to GRE
class Attachment(GUSObject):
    def create(self, case_number):
        self.query_object("Attachment")
        if case_number:
            if type(case_number) == list:
                case_number = ",".join(case_number)
            if "," in case_number:
                get_case_id = Case(filters=is_in("CaseNumber", bracket(case_number))).create()
                self.filters(is_in("ParentId", bracket(get_case_id)))
            else:
                get_case_id = Case(filters=equals("CaseNumber", case_number)).create()
                self.filters(equals("ParentId", get_case_id))
        return self.generate()


# Query the CaseId by the Case Number provided (single or a list), or simply CaseIds that are related to GRE
class Case(GUSObject):
    def create(self):
        self.query_object("Case")
        return self.generate()


# Query the CaseComment based on CommentId, CaseId, or simply the CommentIds that are related to GRE
class CaseComment(GUSObject):
    def create(self, case_number=None):
        self.query_object("CaseComment")
        if case_number:
            if type(case_number) == list:
                case_number = ",".join(case_number)
            if "," in case_number:
                self.filters(is_in("ParentId", bracket(case_number)))
            else:
                self.filters(equals("ParentId", case_number))
        return self.generate()


# Query the CaseComment based on CommentId, CaseId, or simply the CommentIds that are related to GRE
class Chatter(GUSObject):
    def create(self, case_id=None):
        self.query_object("Chatter")
        if case_id:
            if type(case_id) == list:
                case_id = ",".join(case_id)
            if "," in case_id:
                self.filters(is_in("ParentId", bracket(case_id)))
            else:
                self.filters(equals("ParentId", case_id))
        return self.generate()


# Query the CaseId by the Case Number provided (single or a list), or simply CaseIds that are related to GRE
class CIStep(GUSObject):
    def create(self, case_number):
        self.query_object("CIStep")
        if case_number:
            if type(case_number) == list:
                case_number = ",".join(case_number)
            if "," in case_number:
                get_case_id = Case(filters=is_in("CaseNumber", bracket(case_number))).create()
                self.filters(is_in("Case__c", bracket(get_case_id)))
            else:
                get_case_id = Case(filters=equals("CaseNumber", case_number)).create()
                self.filters(equals("Case__c", get_case_id))
        return self.generate()


# Query the CaseId by the Case Number provided (single or a list), or simply CaseIds that are related to GRE
class ClusterInstanceLink(GUSObject):
    def create(self):
        self.query_object("CTCLock")
        return self.generate()


# Query the CaseId by the Case Number provided (single or a list), or simply CaseIds that are related to GRE
class CTCLock(GUSObject):
    def create(self):
        self.query_object("CTCLock")
        return self.generate()


# Query ScrumTeamMember attributes based on Team Name, or simply the Member Names in GRE
class ScrumMember(GUSObject):
    def create(self, team_name=None):
        self.query_object("ScrumMember")
        if team_name:
            if type(team_name) == list:
                team_name = ",".join(team_name)
            if "," in team_name:
                self.filters(is_in(obj['ScrumMember']['TeamName'], bracket(team_name)))
            else:
                self.filters(equals(obj['ScrumMember']['TeamName'], team_name))
        return self.generate()


# Query the attributes of the User based on their individual UserIds
class User(GUSObject):
    def create(self):
        self.query_object("User")
        return self.generate()


# Query the CaseId by the Case Number provided (single or a list), or simply CaseIds that are related to GRE
class Release(GUSObject):
    def create(self):
        self.query_object("Release")
        return self.generate()


class ReleaseEvent(GUSObject):
    def create(self, case_number=None):
        self.query_object("ReleaseEvent")
        if case_number:
            if type(case_number) == list:
                case_number = ",".join(case_number)
            if "," in case_number:
                get_case_id = Case(filters=is_in("CaseNumber", bracket(case_number))).create()
                self.filters(is_in("ChangeCase__c", bracket(get_case_id)))
            else:
                get_case_id = Case(filters=equals("CaseNumber", case_number)).create()
                self.filters(equals("ChangeCase__c", get_case_id))
        return self.generate()


# Activity History within the Change Case (important for GL status)
class Task(GUSObject):
    def create(self, case_id):
        self.query_object("Task")
        if case_id:
            if type(case_id) == list:
                case_id = ",".join(case_id)
            if "," in case_id:
                self.filters(is_in("WhatId", bracket(case_id)))
            else:
                self.filters(equals("ParentId", case_id))
        return self.generate()


class InstanceDatacenter(GUSObject):
    def create(self):
        self.query_object("InstanceDatacenter")
        return self.generate()


# TODO deprecate this in v2.0
# Query the CaseId by the Case Number provided (single or a list), or simply CaseIds that are related to GRE
# class Case:
#     def __init__(self, fields=None, filters=None, limit=None, sort_by=None, sort_seq=None):
#         self.field_value = "Id"
#         self.fields(fields)
#         self.filters(filters)
#         self.limit(limit)
#         self.sort(sort_by, sort_seq)
#
#     def fields(self, fields):
#         if type(fields) == str:
#             self.field_value = fields
#         elif type(fields) == list:
#             self.field_value = ",".join(fields)
#         else:
#             raise TypeError(f"[Case] Fields specified must be 'str' or 'list' type, not {str(type(fields))}")
#
#     def filters(self, filters):
#         self.filter_value = filters
#
#     def limit(self, num=15):
#         self.limit_value = num
#
#     def sort(self, field, seq="DESC"):
#         self.sort_by = field
#         self.sort_seq = seq
#
#     def create(self):
#         case_details = Query("Case").create(
#             fields=self.field_value,
#             filters=self.filter_value,
#             sort_by=self.sort_by,
#             sort_seq=self.sort_seq,
#             limit=self.limit_value
#         )
#         return case_details
#
#
# class CreateQuery:
#     def __init__(self, obj_name):
#         if obj_name in obj:
#             self.obj = obj[obj_name]["Object"]
#
#     def create(self, fields, filters, inclusive=True):
#         try:
#             query = "SELECT " + fields + \
#                     " FROM " + self.obj + \
#                     " WHERE ("
#             for param in filters:
#                 if filters.index(param) == len(filters) - 1:
#                     query += param + ")"
#                 else:
#                     if inclusive:
#                         query += param + " OR "
#                     else:
#                         query += param + " AND "
#             return query
#         except Exception as e:
#             logging.error(e)
#
#
# # Query the CaseComment based on CommentId, CaseId, or simply the CommentIds that are related to GRE
# class CaseComment:
#     def __init__(self, comment_id=None, case_number=None):
#         self.comment_id = comment_id
#         self.case_number = case_number
#         self.default = "Id"
#
#     def from_single(self, fields=None):
#         if not fields:
#             fields = self.default
#         if self.comment_id:
#             comment_details = CreateQuery("CaseComment").create(fields=fields,
#                                                                 filters=["Id = " + quote(self.comment_id)],
#                                                                 inclusive=True)
#         else:
#             cases = Case(self.case_number).from_single("Id")
#             comment_details = CreateQuery("CaseComment").create(fields=fields,
#                                                                 filters=["ParentId IN " + bracket(cases)],
#                                                                 inclusive=True)
#         return comment_details
#
#     def from_multiple(self, fields=None):
#         if not fields:
#             fields = self.default
#         if self.comment_id:
#             comment_details = CreateQuery("CaseComment").create(fields=fields,
#                                                                 filters=["Id IN " + quote(self.comment_id)],
#                                                                 inclusive=True)
#         else:
#             cases = Case(self.case_number).from_multiple("Id")
#             comment_details = CreateQuery("CaseComment").create(fields=fields,
#                                                                 filters=["ParentId IN " + bracket(cases)],
#                                                                 inclusive=True)
#         return comment_details
#
#     def gre(self, fields=None):
#         if not fields:
#             fields = self.default
#         gre_case_ids = Case().gre("Id")
#         comment_details = CreateQuery("CaseComment").create(fields=fields,
#                                                             filters=["ParentId IN " + bracket(gre_case_ids)],
#                                                             inclusive=True)
#         return comment_details
#
#
# # Query ScrumTeamMember attributes based on Team Name, or simply the Member Names in GRE
# class ScrumMember:
#     def __init__(self, team_name=None):
#         self.team_name = team_name
#         self.default = obj['ScrumMember']["MemberName"]
#
#     def from_single(self, fields=None):
#         if not fields:
#             fields = self.default
#         team_members = CreateQuery("ScrumMember").create(fields=fields,
#                                                          filters=[obj['ScrumMember']['TeamName'] + " = "
#                                                                   + quote(self.team_name)],
#                                                          inclusive=True)
#         return team_members
#
#     def gre(self, fields=None):
#         if not fields:
#             fields = self.default
#         team_members = CreateQuery("ScrumMember").create(fields=fields,
#                                                          filters=[obj['ScrumMember']['TeamName'] + " = "
#                                                                   + quote('Global Release Engineering')],
#                                                          inclusive=True)
#         return team_members
#
#
# # Query the attributes of the User based on their individual UserIds
# class User:
#     def __init__(self, user_id=None):
#         self.user_id = user_id
#         self.default = "Name"
#
#     def get_single(self, fields=None):
#         if not fields:
#             fields = self.default
#         users = CreateQuery("User").create(fields=fields,
#                                            filters=["Id = " + quote(self.user_id)],
#                                            inclusive=True)
#         return users
#
#     def get_multiple(self, fields=None):
#         if not fields:
#             fields = self.default
#         users = CreateQuery("User").create(fields=fields,
#                                            filters=["Id IN " + bracket(self.user_id)],
#                                            inclusive=True)
#         return users
#
#     def gre(self, fields=None):
#         if not fields:
#             fields = self.default
#         team = ScrumMember().gre()
#         users = CreateQuery("User").create(fields=fields,
#                                            filters=["Id IN " + bracket(team)],
#                                            inclusive=True)
#         return users
#
#
# class ReleaseEvent:                    # TODO LOGGING exception for no case_id
#     def __init__(self, case_id=None):
#         self.case_id = case_id
#         self.default = obj['ReleaseEvent']['Case']
#
#     def from_single(self, fields=None, date=None, shift="SIN"):
#         release_event_details = None
#         if not fields:
#             fields = self.default
#         if date:
#             shift_start, shift_end = self.initial_date(date=date, shift=shift.upper())
#             if shift_start:
#                 release_event_details = CreateQuery("ReleaseEvent").create(fields=fields,
#                                                                            filters=[obj['ReleaseEvent']['Case'] + " = "
#                                                                                     + quote(self.case_id),
#                                                                                     obj['ReleaseEvent']['Start'] + " < "
#                                                                                     + shift_end,
#                                                                                     obj['ReleaseEvent']['End'] + " > "
#                                                                                     + shift_start],
#                                                                            inclusive=False)
#         else:
#             release_event_details = CreateQuery("ReleaseEvent").create(fields=fields,
#                                                                        filters=[obj['ReleaseEvent']['Case'] + " = "
#                                                                                 + quote(self.case_id)],
#                                                                        inclusive=True)
#         return release_event_details
#
#     def from_multiple(self, fields=None):
#         if not fields:
#             fields = self.default
#         release_event_details = CreateQuery("ReleaseEvent").create(fields=fields,
#                                                                    filters=[obj['ReleaseEvent']['Case'] + " IN "
#                                                                             + bracket(self.case_id)],
#                                                                    inclusive=True)
#         return release_event_details
#
#     def initial_date(self, date, shift):
#         if not date:
#             date = datetime.datetime.utcnow()
#         else:
#             date = datetime.datetime.strptime(date, "%Y-%m-%d")
#         shift_start, shift_end = ShiftParser(date, shift).get_shifts()
#         return shift_start, shift_end
#
#     def gre(self, fields=None, date=None, shift="SIN"):
#         if not fields:
#             fields = self.default
#         cases = Case().gre("Id")
#         shift_start, shift_end = self.initial_date(date=date, shift=shift)
#         if shift_start:
#             release_event_details = CreateQuery("ReleaseEvent").create(fields=fields,
#                                                                        filters=[obj['ReleaseEvent']['Case'] + " IN "
#                                                                                 + bracket(cases),
#                                                                                 obj['ReleaseEvent']['Start'] + " < "
#                                                                                 + shift_end,
#                                                                                 obj['ReleaseEvent']['End'] + " > "
#                                                                                 + shift_start],
#                                                                        inclusive=False)
#         else:
#             release_event_details = None
#         return release_event_details
#
#
# class Task:
#     def __init__(self, case_id=None):
#         self.case_id = case_id
#         self.default = "Subject"
#
#     def from_single(self, fields=None):
#         if not fields:
#             fields = self.default
#         task_details = CreateQuery("Task").create(fields=fields,
#                                                   filters=[obj['Task']['Case'] + " = " + quote(self.case_id)],
#                                                   inclusive=True)
#         return task_details
#
#     def from_multiple(self, fields=None):
#         if not fields:
#             fields = self.default
#         task_details = CreateQuery("Task").create(fields=fields,
#                                                   filters=[obj['Task']['Case'] + " IN " + bracket(self.case_id)],
#                                                   inclusive=True)
#         return task_details
#
#     def gre(self, fields=None):
#         if not fields:
#             fields = self.default
#         cases = Case().gre("Id")
#         task_details = CreateQuery("Task").create(fields=fields,
#                                                   filters=[obj['Task']['Case'] + " IN " + bracket(cases)],
#                                                   inclusive=True)
#         return task_details
#
#
# class InstanceDatacenter:
#     def __init__(self):
#         self.default = "Pod_Name__c"
#
#     def gre(self, fields=None):
#         if not fields:
#             fields = self.default
#         instance_details = CreateQuery("InstanceDatacenter").create(fields=fields,
#                                                                     filters=[obj['InstanceDatacenter']['Lifecycle'] + " LIKE " + quote("%Go Live%")],
#                                                                     inclusive=True)
#         return instance_details


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