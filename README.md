# guspy
[![Version](https://img.shields.io/badge/version-v2.01-blue)](https://git.soma.salesforce.com/cherdon-liew/Taskmaster)

Gus Python library that allows for simple SOQL queries on GUS, as well as Authentication to GUS.

Current Version: `2.01`

** There is a substantial change to the format of querying in v2.0+, where it allows for more specific filters and arrangement of the data acquired from GUS

## Installation
To install, simply use your virtualenv:

```
pip install guspy
```

## Repackaging Instructions
To repackage, change the version number of the `setup.py` file
```
python3 setup.py bdist_wheel
python3 -m twine upload dist/*
```


## Summary

Example:
```
query = Case(
    fields=<FIELDS REQUIRED (list or str)>,
    filters=<FILTERS EXPECTED>,
    limit=<TOTAL NUMBER OF RESULTS>,
    sort_by=<FIELD TO SORT BY>,
    sort_seq=<ASC or DESC>
)
```

**Filters**
-------------
`Filters` help to improve the specificity of the query that you want. Similar to excel commands, you encapsulate everything in brackets ()
```
from guspy.filters import *

## Equals ##
equals("CaseNumber", "8938202")
# Returns "CaseNumber = '8938202'"

## Within ##
is_in("CaseNumber", ["8190582","8190583"])
# Returns "CaseNumber IN ('8190582','8190583')"

## Like ##
like("CaseNumber", "389*", identifier="*")
# Returns "CaseNumber LIKE '389%'"
# This means to return all items that CaseNumber starts with 389

## Including ##
incl(filter_1, filter_2, filter_3)
# Returns "filter_1 AND filter_2 AND filter_3"

## Excluding ##
excl(filter_1, filter_2, filter_3)
# Returns "filter_1 OR filter_2 OR filter_3"

## Quote ##
quote(938859)
# Returns "'938859'"

## Bracket ##
bracket(938859)
# Returns "(938859)"
```

**General Object**
-------------
For GUS Objects not found in the document below, you can find out what the name of the GUS Object is, and call the query similarly with the following commands:
```
from guspy import GUSObject
object = GUSObject(fields=<FIELDS>, filters=<FILTERS>)
object.query_object(<NAME OF GUS OBJECT>)
query = object.generate()
```

**Apprise Object**
-------------
To be updated

**Attachment Object**
-------------
To be updated

**Cases Object**
-------------
`Case` class can be initialised with the case number or list of case numbers. In which the single case_number would be using `from_single` method, and the list of case_numbers will be using the `from_multiple` method.
```
from guspy import Case
query = Case(
    fields="Id, CaseNumber, Release__c",
    filters=is_in(CaseNumber, ["8190582","8190583"]),
    sort_by="LastModified",
    sort_seq="DESC"
)
query = Case(
    fields="Id, CaseNumber, Release__c",
    filters=equals(CaseNumber, "8190582"),
    sort_by="LastModified",
    sort_seq="DESC"
)
```

**CaseComments Object**
-------------
To be updated

**Chatter Object**
-------------
To be updated

**CIStep Object**
-------------
To be updated

**ClusterInstanceLink Object**
-------------
To be updated

**CTCLock Object**
-------------
To be updated

**ScrumMember Object**
-------------
To be updated

**User Object**
-------------
To be updated

**Release Object**
-------------
To be updated

**ReleaseEvent Object**
-------------
To be updated

**Task Object**
-------------
To be updated

**InstanceDatacenter Object**
-------------
To be updated

**Logging In**
-------------
```
from guspy.access import Gus
gus = Gus(username=<USERNAME@ORGANIZATION>,
          password=<PASSWORD>,
          otp=<2FA TOKEN>).connect()
```
Take note to login with the organization provided. For internal salesforce users, either use @salesforce.com or @gus.com, etc.

Upon logging in, use the commands above to get the query string for the object required (CaseComments, ReleaseEvents, etc.) before executing the following command:
```
gus.raw(<REQUIRED_QUERY>)
gus.parse(<REQUIRED_QUERY>)
```
Where `raw` will return the raw data, and `parse` will return in a DataFrame format.

If unable to access after a certain time, please execute the following with a fresh 2FA token to reconnect:
```
gus.reconnect(otp=<2FA TOKEN>)
```