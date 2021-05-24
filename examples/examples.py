from guspy.access import Gus
from guspy import CreateQuery, Case, CaseComment


# Creating the connection to GUS
username = "username@gus.com"
password = "123456789"
gus = Gus(username=username,
          password=password)
conn = gus.connect()


# Creating a SOQL query
query1 = CreateQuery("release").create(fields='Id',
                                      filters=["ParentId = '02801523'"],
                                      inclusive=True)
""" SELECT Id FROM ADM_Release__c WHERE ParentId = '02801523' """


# Creating a query for Cases
query2 = Case('02801523').get_single("Id")
""" SELECT Id FROM Case WHERE CaseNumber = '108983' """

query3 = Case(['02801523', '02801524']).get_multiple("Id")
""" SELECT Id FROM Case WHERE CaseNumber IN ['02801523', '02801524'] """

query4 = Case().gre("Id, CaseNumber")
""" SELECT Id, CaseNumber FROM Case WHERE 
    (Team_Lookup__c = 'Global Release Engineering' AND Team_Lookup__c = 'Release Management') """


# Creating a query for CaseComments
query5 = CaseComment(comment_id="00aB0000009fiZZIAY").get_single("Id")
""" SELECT Id FROM CaseComments WHERE Id = '00aB0000009fiZZIAY' """

query6 = CaseComment(case_number="02801523").get_single("Id")
""" SELECT Id FROM CaseComment WHERE (ParentId IN (SELECT Id FROM Case WHERE (CaseNumber = '02801523'))) """

query7 = CaseComment().gre("Id, CommentBody")
"""SELECT Id, CommentBody FROM CaseComment 
    WHERE (ParentId IN (SELECT Id FROM Case 
    WHERE (Team_Lookup__c = 'Release Management' OR Team_Lookup__c = 'Global Release Engineering')))"""