from simple_salesforce import Salesforce, SalesforceLogin
from simple_salesforce.exceptions import SalesforceAuthenticationFailed, SalesforceExpiredSession
import pandas as pd

GUS_BASE_URL = "https://gus.my.salesforce.com"
GUS_CHATTER_FEED_URL = f"{GUS_BASE_URL}/services/data/v40.0/chatter/feed-elements"


class Gus:
    def __init__(self, username, password, otp=None):
        self.username = username
        self.password = password
        self.otp = otp
        self.session_id, self.instance = None, None
        self.soql = self.connect()

    def get_instance(self, otp=None):
        if otp:
            self.otp = otp
        try:
            if self.otp:
                self.session_id, self.instance = SalesforceLogin(username=self.username,
                                                                 password=self.password + "." + self.otp)
            else:
                self.session_id, self.instance = SalesforceLogin(username=self.username,
                                                                 password=self.password)
        except Exception as e:
            print(e)                                # TODO ERROR LOGGING IN
        return self.session_id, self.instance

    def connect(self):
        session_id, instance = self.get_instance(otp=self.otp)
        if instance:
            return Salesforce(session_id=session_id,
                              instance=instance)
        elif SalesforceAuthenticationFailed:
            print("Authentication Failed, please check guspy")
            # TODO ERROR CONNECTING INSTANCE
            return None

    def reconnect(self, otp=None):
        if otp:
            self.otp = otp
            session_id, instance = self.get_instance(otp=otp)
        else:
            session_id, instance = self.get_instance()
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
            self.soql = self.reconnect()
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

    def update_work(self, id, body):
        if not id or not body:
            raise "[GUSPY] Both work ID and body are required to update the work item"
        try:
            self.soql.ADM_Work__c.update(id, body)
        except SalesforceExpiredSession as error:
            self.soql = self.reconnect()
            self.soql.ADM_Work__c.update(id, body)
        except Exception as e:
            raise f"Seems like there was en error while updating the work: {e}"

    def chatter(self, data):
        if type(data) != dict:
            raise f"Please return a dict object with at least body and subjectId"
        else:
            try:
                res = self.soql._call_salesforce("POST", url=GUS_CHATTER_FEED_URL, data=json.dumps(data))
                return res
            except SalesforceExpiredSession as error:
                self.soql = self.reconnect()
                res = self.soql._call_salesforce("POST", url=GUS_CHATTER_FEED_URL, data=json.dumps(data))
                return res
            except Exception as e:
                raise f"Chattering failed: {e}"

    def get_attachment(self, attachment_url):
        try:
            url = f"{GUS_BASE_URL}{attachment_url}"
            bearer = "Bearer " + self.session_id
            header = {'Content-Type': 'application/json', 'Authorization': bearer, 'Connection': 'close'}
            b_attachment_data = requests.get(url, headers=header).content
            attachment = b_attachment_data.decode("utf-8")
        except SalesforceExpiredSession as error:
            self.soql = self.reconnect()
            url = f"{GUS_BASE_URL}{attachment_url}"
            bearer = "Bearer " + self.session_id
            header = {'Content-Type': 'application/json', 'Authorization': bearer, 'Connection': 'close'}
            b_attachment_data = requests.get(url, headers=header).content
            attachment = b_attachment_data.decode("utf-8")
        return attachment
