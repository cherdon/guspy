from simple_salesforce import Salesforce, SalesforceLogin
import pandas as pd


class Gus:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.soql = self.connect()

    def get_instance(self):
        try:
            session_id, instance = SalesforceLogin(username=self.username,
                                                   password=self.password)
        except Exception as e:
            session_id, instance = None, None
            print(e)                                # TODO ERROR LOGGING IN
        return session_id, instance

    def connect(self):
        session_id, instance = self.get_instance()
        if instance:
            return Salesforce(session_id=session_id,
                              instance=instance)
        else:
            # TODO ERROR CONNECTING INSTANCE
            return None

    def raw(self, query):
        data = self.soql.query_all(query)['records']
        return data

    def parse(self, query):
        data = self.raw(query)
        data = pd.DataFrame(data)
        if data.empty:
            pass
        else:
            data = data.drop('attributes', axis=1)
        return data
