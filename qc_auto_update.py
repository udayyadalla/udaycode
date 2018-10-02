## ALM QC Auto Update##
__author__='Uday'
import re
import json
import requests
import datetime
import time
import sys
import xmltodict
from requests.auth import HTTPBasicAuth

#protractor_result_file = './combined_result.json'

almUserName = "Username"
almPassword = "Password"
almDomain = "DEFAULT"
almProject = "Project_name"
build_id = 'build Id to update'

almURL = "http://bill.qa.shoretel.com/qcbin/"
authEndPoint = almURL + "authentication-point/alm-authenticate"
qcSessionEndPoint = almURL + "rest/site-session"
qcLogoutEndPoint = almURL + "authentication-point/logout"
midPoint = "rest/domains/" + almDomain + "/projects/" + almProject

#mydate = datetime.datetime.now()
testSetName = ""
assignmentGroup = ""
parser_temp_dic = {}

cookies = dict()

headers = {
    'cache-control': "no-cache"
}

def alm_login():
    print('---------------alm_login')
    payload = "<alm-authentication><user>" + almUserName + "</user><password>" + almPassword + "</password></alm-authentication>"
    print("payload::",payload)
    response = requests.post(authEndPoint, payload)
    print("response::",response)
    if response.status_code == 200:
        cookieName = response.headers.get('Set-Cookie')
        print("cookieName::",cookieName)
        LWSSO_COOKIE_KEY = cookieName[cookieName.index("=") + 1: cookieName.index(";")]
        print("LWSSO_COOKIE_KEY",LWSSO_COOKIE_KEY)
        cookies['LWSSO_COOKIE_KEY'] = LWSSO_COOKIE_KEY
    response = requests.post(qcSessionEndPoint, headers=headers, cookies=cookies)
    if response.status_code == 200 | response.status_code == 201:
        cookieName = response.headers.get('Set-Cookie').split(",")[1]
        QCSession = cookieName[cookieName.index("=") + 1: cookieName.index(";")]
        cookies['QCSession'] = QCSession
    return 'login successful'

def find_test_set_folder(test_set_path):
    print("--------------find-----------")
    id = find_folder_id(test_set_path.split("\\"), "test-set-folders", 0, "id")
    print(id)
    sub_folders = find_sub_test_set_folder(id,"test-set-folders")
    print("find_test_set_folder_sub_folders::",sub_folders)
    set_ids = find_test_sets(sub_folders,'test-sets')
    print("set_ids::",set_ids)
    tcid = find_test_cases(set_ids, 'test-instances')
    print("tcid",tcid)
    update_testcases(tcid, 'test-instances', build_id)

def find_folder_id(arrFolder, strAPI, parentID, fields):
    response = ""
    for folderName in arrFolder:
        payload = {"query": "{name['" + folderName + "'];parent-id[" + str(parentID) + "]}", "fields": fields}
        print("payload::",payload)
        response = requests.get(almURL + midPoint + "/" + strAPI, params=payload, headers=headers, cookies=cookies)
        print("response::",response)
        obj = xmltodict.parse(response.content)
        print("obj",obj)
        if int(obj['Entities']["@TotalResults"]) >= 1:
            print("---IF BLOCK---")
            parentID = obj['Entities']['Entity']['Fields']['Field']['Value']
            print('parentID::',parentID)
        else:
            print('---ELSE BLOCK---')
            data = "<Entity Type=" + chr(34) + strAPI[0:len(strAPI) - 1] + chr(34) + "><Fields><Field Name=" + chr(
                34) + "name" + chr(
                34) + "><Value>" + folderName + "</Value></Field><Field Name=" + chr(34) + "parent-id" + chr(
                34) + "><Value>" + str(parentID) + "</Value></Field></Fields> </Entity>"
            response = requests.post(almURL + midPoint + "/" + strAPI, data=data, headers=headers, cookies=cookies)
            obj = xmltodict.parse(response.content)
            if response.status_code == 200 | response.status_code == 201:
                parentID = obj['Entities']['Entity']['Fields']['Field']['Value']
                print("parentID::",parentID)
    return parentID

def find_sub_test_set_folder(parentID,strAPI):
    payload = {"query": "{parent-id[" + str(parentID) + "]}"}
    print("payload::",payload)
    response = requests.get(almURL + midPoint + "/" + strAPI, params=payload, headers=headers, cookies=cookies)
    print("response::",response)
    ee = xmltodict.parse(response.content)
    print("find_sub_test_set_folder_ee::",ee)
    sub_folders = []
    for item in range(int(ee['Entities']['@TotalResults'])):
        sub_folders.append(ee['Entities']['Entity'][item]['Fields']['Field'][8]['Value'])
    return sub_folders

def find_test_sets(parentIDs,strAPI):
    sub_sets = []
    for item in parentIDs:
        payload = {"query": "{parent-id[" + str(item) + "]}"}
        print("find_test_sets_payload::",payload)
        response = requests.get(almURL + midPoint + "/" + strAPI, params=payload, headers=headers, cookies=cookies)
        print("find_test_sets__response::", response)
        print("find_test_sets__strAPI::_",strAPI)
        ee = xmltodict.parse(response.content)
        if int(ee['Entities']['@TotalResults']) == 1 :
            sub_sets.append(ee['Entities']['Entity']['Fields']['Field'][10]['Value'])
        else :
            for item in range(int(ee['Entities']['@TotalResults'])):
                sub_sets.append(ee['Entities']['Entity'][item]['Fields']['Field'][10]['Value'])
    # print(len(sub_sets),sub_sets)
    return sub_sets

def find_test_cases(parentIDs,strAPI):
    test_cases = []
    for item in parentIDs:
        payload = {"query": "{contains-test-set.id[" + str(item) + "]}"}
        print("payload::", payload)
        response = requests.get(almURL + midPoint + "/" + strAPI, params=payload, headers=headers, cookies=cookies)
        print("response::", response)
        ee = xmltodict.parse(response.content)
        print(ee)
        if int(ee['Entities']['@TotalResults']) == 1 :
            test_cases.append(ee['Entities']['Entity']['Fields']['Field'][13]['Value'])
        else :
            for item in range(int(ee['Entities']['@TotalResults'])):
                test_cases.append(ee['Entities']['Entity'][item]['Fields']['Field'][13]['Value'])
    return test_cases

def update_testcases(casesIDs,strAPI,build_id):
    for item in casesIDs:
        payload = """<Entity Type="test-instance"><Fields><Field Name="status"><Value>Passed</Value></Field><Field Name="actual-tester"><Value>"""+ almUserName +"""</Value></Field><Field Name="user-01"><Value>"""+ build_id +"""</Value></Field></Fields><RelatedEntities/></Entity>"""
        print("payload::", payload)
        headers["Content-Type"] = "application/xml"
        response = requests.put(almURL + midPoint + "/" + strAPI + "/" + item, data=payload, headers=headers, cookies=cookies)
        print("response::", response)
        print(response.status_code)

print(alm_login())
#find_test_set_folder('Root\Cosmo 1.0\Drop 4\Regression Testing\\3. PRODUCTION REGRESSION\oo. R1808 (CR32)  - 21.90.9700.0 & 804.1808.1000.0 - July 30 Due Date August 16 2018\Automated Testing - R1808 phase - Surendra\Automation test - ST VTF\Cosmo VTF_ST Automation_21.90.9700.0\IPPhone')
# find_sub_test_set_folder(184441,"test-set-folders")
# find_test_sets(['184442', '184443', '184444', '184445', '184446', '184447', '184448', '184449', '184450'],'test-sets')
#find_test_sets(['184442'],'test-sets')
# find_test_cases(['469051', '469052', '469053', '469054', '469055', '469056', '469057', '469058', '469059', '469060', '469061', '469062', '469063', '469064', '469065', '469066', '469067', '469068', '469069', '469070', '469071', '469072', '469073', '469074', '469075', '469076', '469077', '469078', '469079', '469080', '469081', '469082', '469083', '469084', '469085', '469086', '469087', '469088', '469089', '469090', '469091', '469092', '469093', '469094', '469095', '469096', '469097', '469098', '469099', '469100', '469101', '469102', '469103', '469104', '469105', '469106', '469107', '469108', '469109', '469110', '469111', '469112', '469113', '469114', '469115', '469116', '469117', '469118', '469119', '469120', '469121', '469122', '469123', '469124', '469125', '469126', '469127'],'test-instances')
#find_test_cases(['469051', '469052'],'test-instances')
# update_testcases(['3873399'],'test-instances','21.12.2200.0')
find_test_set_folder('Root\Cosmo 1.0\Cosmo RR (Rolling Release) Regression Testing\j. 21.9009.1800.0 & 804.180x.0 - MT DSR & ST PHP Upgrade 7.2 testing - due July 20, 2018\\1. Automated Testing - CosmoRR phase - Surendra\Automation test - ST VTF\Cosmo VTF_ST Automation_21.9008.9700.0\IPPhone')

