from simple_salesforce import Salesforce, SalesforceLogin
from simple_salesforce.exceptions import SalesforceAuthenticationFailed, SalesforceExpiredSession
import pandas as pd


class Gus:
    def __init__(self, username, password, otp=None):
        self.username = username
        self.password = password
        self.otp = otp
        self.soql = self.connect()

    def get_instance(self, otp=None):
        if otp:
            self.otp = otp
        try:
            session_id, instance = SalesforceLogin(username=self.username,
                                                   password=self.password + "." + self.otp)
        except Exception as e:
            session_id, instance = None, None
            print(e)                                # TODO ERROR LOGGING IN
        return session_id, instance

    def connect(self):
        session_id, instance = self.get_instance(otp=self.otp)
        if instance:
            return Salesforce(session_id=session_id,
                              instance=instance)
        elif SalesforceAuthenticationFailed:
            print("Authentication Failed, please check guspy")
            # TODO ERROR CONNECTING INSTANCE
            return None

    def reconnect(self, otp):
        self.otp = otp
        session_id, instance = self.get_instance(otp=self.otp)
        if instance:
            return Salesforce(session_id=session_id,
                              instance=instance)
        elif SalesforceAuthenticationFailed:
            print("Authentication Failed, please check guspy")
            # TODO ERROR CONNECTING INSTANCE
            return None

    def raw(self, query):
        try:
            data = self.soql.query_all(query)['records']
        except SalesforceExpiredSession as error:
            self.soql = self.connect()
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
