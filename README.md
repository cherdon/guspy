# guspy
Gus Python library that allows for simple SOQL queries on GUS, as well as Authentication to GUS.

Current Version: `1.22`

**Quickfix Applied on Major Version 1.0 for dependencies changes to 2FA authentication. Now, you need to access with your 2FA password in the Salesforce Authenticator.

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
query = Case(<SPECIFICATIONS OF OBJECT>).from_single(<FIELDS REQUIRED>)
```
All queries on the objects can be summarised to accept parameters in two places (except special conditions such as GRE specific objects)
The first is the specifications of the object itself (e.g. Case Number, etc) whereas the second is the fields required to be shown.


**Cases Object**
-------------
`Case` class can be initialised with the case number or list of case numbers. In which the single case_number would be using `from_single` method, and the list of case_numbers will be using the `from_multiple` method.
```
from guspy import Case
query = Case("8190582").from_single("Id")
query = Case(["8190582","8190583"]).from_multiple("Id")
```

Special: GRE Cases can be simply queried.
```
gre_query = Case().gre("Id, CaseNumber")
```


**CaseComments Object**
-------------
`CaseComment` object can be initialised with either `case_number` or `comment_id`, in which similar to the `Case` object, would be using `from_single` or `from_multiple` functions to get a single case/comment or multiple case/comment respectively
```
from guspy import CaseComment
query = CaseComment(case_number="").from_single("Id")
query = CaseComment(case_number=["8190582","8190583"]).from_multiple("Id")
```

Special: GRE Cases can be simply queried
```
query = CaseComment().gre("Id, CommentBody")
```

**ScrumMember Object**
-------------
`ScrumMember` object can be initialised with `team_name`, in which you can use `from_single` function to get attributes of the Scrum Members
```
from guspy import ScrumMember
query = ScrumMember(team_name="").from_single("Id")
```

Special: GRE Cases can be simply queried
```
query = ScrumMember().gre("Id, Name")
```

**User Object**
-------------
`User` object can be initialised with `user_id`, in which you can use `from_single` or `from_multiple` functions to get attributes of the Users
```
from guspy import User
query = User(user_id="").from_single("Id")
query = User(user_id=["8190582","8190583"]).from_multiple("Id")
```

Special: GRE Cases can be simply queried
```
query = User().gre("Id, Division")
```

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