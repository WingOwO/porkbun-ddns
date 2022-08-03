import json
import requests
import sys

PING_API = "https://porkbun.com/api/json/v3/ping"
CREATE_RECORD_API = "https://porkbun.com/api/json/v3/dns/create/"
GET_RECORDS_API = "https://porkbun.com/api/json/v3/dns/retrieve/"
DEL_RECORD_API = "https://porkbun.com/api/json/v3/dns/delete/"

class ApiConfig:
    apikey : str
    secretapikey : str

    def __init__(self, key : str, secret : str):
        self.apikey = key
        self.secretapikey = secret
        pass

class PorkbunDDns:

    apiConfigJson : str
    rootDomain : str

    def __init__(self, rootDomain : str, key : str, secret : str):
        self.apiConfigJson = json.dumps(ApiConfig(key, secret).__dict__)
        self.rootDomain = rootDomain
        pass

    def getMyIP(self):
        ping = json.loads(requests.post(PING_API, data = self.apiConfigJson).text)
        return ping["yourIp"]

    def getMyIPv6(self):
        ping = json.loads(requests.post("http://v6.ip.zxinc.org/info.php?type=json").text)
        return ping["data"]["myip"]

    def getRecords(self): #grab all the records so we know which ones to delete to make room for our record. Also checks to make sure we've got the right domain
        allRecords=json.loads(requests.post(GET_RECORDS_API + rootDomain, data = self.apiConfigJson).text)
        if allRecords["status"]=="ERROR":
            print('Error getting domain. Check to make sure you specified the correct domain, and that API access has been switched on for this domain.');
            sys.exit();
        return allRecords

    def createRecord(self, subDomain : str, myIp : str, recordType : str):
        requestData = json.loads(self.apiConfigJson)
        requestData.update({'name': subDomain, 'type': recordType, 'content': myIp, 'ttl': 300})
        url = CREATE_RECORD_API + self.rootDomain
        print("Creating record: " + self.getFullDomain(subDomain) + " with answer of " + myIp)
        responseData = json.loads(requests.post(url, data = json.dumps(requestData)).text)
        print(responseData)
        pass

    def updateRecord(self, subDomain : str, myIp : str, recordType : str):
        needDeleteDomain = self.getFullDomain(subDomain)
        self.deleteRecord(needDeleteDomain, recordType)
        self.createRecord(subDomain, myIp, recordType)
        pass


    def deleteRecord(self, needDeleteDomain : str, recordType : str):
        for item in self.getRecords()["records"]:
            if item["name"] == needDeleteDomain and item["type"] == recordType:
                print("Deleting existing " + item["type"] + " Record")
                url = DEL_RECORD_API + self.rootDomain + "/" + item["id"]
                responseData = json.loads(requests.post(url, data = self.apiConfigJson).text)
                print(responseData)
            pass
        pass

    def getFullDomain(self, subName : str):
        if subName == "":
            return rootDomain
        return subName + "." + rootDomain


    def myIP(self, recordType : str):
        if recordType == "AAAA":
            return self.getMyIPv6()
        return self.getMyIP()

    pass


if __name__ == '__main__':
    config = json.load(open("config.json"))
    rootDomain = config["rootDomain"]
    apikey = config["apikey"]
    secretapikey = config["secretapikey"]
    records = config["records"]
    ddns = PorkbunDDns(rootDomain, apikey, secretapikey)
    for record in records:
        subDomain = record["subDomain"]
        recordType = record["type"]
        ip = ""
        if "ip" not in record:
            ip = ddns.myIP(recordType)
            pass
        else:
            ip = record["ip"]
            pass
        ddns.updateRecord(subDomain, ip, recordType)
        pass
    pass
