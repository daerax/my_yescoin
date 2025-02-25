import hashlib
import random
import time
import requests
import json
import urllib.parse
from colorama import init, Fore, Style, deinit
init(autoreset=True)
bright = Style.BRIGHT

def parse_and_reconstruct(url_encoded_string):
    parsed_data = urllib.parse.parse_qs(url_encoded_string)
    user_data_encoded = parsed_data.get('user', [None])[0]
    if user_data_encoded:
        user_data_json = urllib.parse.unquote(user_data_encoded)
    else:
        user_data_json = None
    reconstructed_string = f"user={user_data_json}"
    for key, value in parsed_data.items():
        if key != 'user':
            reconstructed_string += f"&{key}={value[0]}"
    return reconstructed_string

def format_task_data(data):
    task_list = data['taskList']
    special_task_list = data['specialTaskList']
    
    formatted_task_list = []
    for task in task_list:
        formatted_task = {
            "taskId": task["taskId"],
            "userId": task["userId"],
            "taskBonusAmount": task["taskBonusAmount"],
            "taskDescription": task["taskDescription"],
            "taskStatus": task["taskStatus"],
            "checkStatus": task["checkStatus"]
        }
        formatted_task_list.append(formatted_task)
    
    formatted_special_task_list = []
    for special_task in special_task_list:
        formatted_special_task = {
            "taskId": special_task["taskId"],
            "userId": special_task["userId"],
            "taskBonusAmount": special_task["taskBonusAmount"],
            "taskDescription": special_task["taskDescription"],
            "taskStatus": special_task["taskStatus"],
            "checkStatus": special_task["checkStatus"]
        }
        formatted_special_task_list.append(formatted_special_task)
    
    formatted_data = {
        "taskList": formatted_task_list,
        "specialTaskList": formatted_special_task_list
    }
    return formatted_data

ACC_FILE = 'query.txt'
def readQuery():
    try:
        with open(ACC_FILE, 'r') as f:
            return [line.strip() for line in f.readlines()]
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"🔴 Error: {e}")
        exit(1)

def fetch(method, url, token=None, data=None, sign=None, tm=None) -> json:
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-ID,en-US;q=0.9,en;q=0.8,id;q=0.7',
        'content-length': '0',
        'priority': 'u=1, i',
        'Origin': 'https://www.yescoin.fun',
        'referer': 'https://www.yescoin.fun/',
        'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36'
    }
    if token:
        headers['token'] = token
    if sign:
        headers['sign'] = sign
        headers['content-length'] = '118'
        headers['content-type'] = 'application/json'
    if tm:
        headers['tm'] = tm
        print(headers)
    attempt = 1 #Initial attempt
    while attempt<=10:
        try:
            res = requests.request(method, url, headers=headers, json=data, timeout=5)
            # print(res.status_code, res.text)
            if res.status_code in [200, 401]:
                return res
            else:
                print(f"🔴 Failure!, {attempt} attempt", end='\r', flush=True)
                # print(res.status_code, res.text)
                print(" " * 120)
            return res
        except Exception as e:
            print(f"🔴 Error: {str(e)}, {attempt} attemp", end='\r', flush=True)
            print(" " * 120)
        attempt += 1

def login(query):
    data = {
        'code': parse_and_reconstruct(query)
    }
    res = fetch('POST', 'https://api-backend.yescoin.fun/user/login', data=data).json()    
    print(f"Login\t\t: 🟢 {res['message'] }")
    return res['data']['token']

def getAccountInfo(token):
    res = fetch('GET', 'https://api-backend.yescoin.fun/account/getAccountInfo', token=token).json()
    # print(f"Account Info\t: {res['data']}")
    print(f"Account Info\t: Balance {res['data']['currentAmount']:,} | {res['data']['levelInfo']['rankName']} Lvl. {res['data']['levelInfo']['level']}")

def getAccountBuildInfo(token):
    res = fetch('GET', 'https://api-backend.yescoin.fun/build/getAccountBuildInfo', token=token).json()
    box = res['data']['specialBoxLeftRecoveryCount']
    coin = res['data']['coinPoolLeftRecoveryCount']
    print(f"Booster\t\t: Special Box: {box} | Coin Pool: {coin}")
    for _ in range(box):
        recoverSpecialBox(token)
    for _ in range(coin):
        recoverCoinPool(token)
    # claimOfflineBonus(token) skip

def getFinishTaskBonusInfo(token):
    dailyRes = fetch('GET', 'https://api-backend.yescoin.fun/task/getFinishTaskBonusInfo', token=token).json()
    dailyCount = f"Daily: {dailyRes['data']['dailyTaskFinishCount']}/{dailyRes['data']['dailyTaskTotalCount']} -> {Fore.GREEN if dailyRes['data']['dailyTaskBonusStatus'] != 0 else Fore.RED}{dailyRes['data']['dailyTaskFinishBonus']}"
    commonCount = f"Common: {dailyRes['data']['commonTaskFinishCount']}/{dailyRes['data']['commonTaskTotalCount']} -> {Fore.GREEN if dailyRes['data']['commonTaskBonusStatus'] != 0 else Fore.RED}{dailyRes['data']['commonTaskFinishBonus']}" 
    print(f"Task \t\t: {dailyCount+Style.RESET_ALL}\n\t\t  {commonCount+Style.RESET_ALL}")

def getTaskList(token):
    res = fetch('GET', f'https://api-backend.yescoin.fun/task/getTaskList', token=token).json()
    hasil = format_task_data(res['data'])
    tab = "\t\t  "
    for key, tasks in hasil.items():
        print(f"{key}\t:")
        for task in tasks:
            if task['checkStatus'] != 1:
                clickTaskRes = fetch('POST', 'https://api-backend.yescoin.fun/task/clickTask', token=token, data=task['taskId']).json()
                print(f"{tab}{task['taskDescription']} {clickTaskRes['message']}", end='\r', flush=True)
                time.sleep(1)
                for _ in range(2):
                    checkTaskRes = fetch('POST', 'https://api-backend.yescoin.fun/task/checkTask', token=token, data=task['taskId']).json()
                    print(f"{tab}{task['taskDescription']} {checkTaskRes['message']}", end='\r', flush=True)
                    time.sleep(3)
                claimTaskRewardRes = fetch('POST', 'https://api-backend.yescoin.fun/task/claimTaskReward', token=token, data=task['taskId']).json()
                print(f"{tab}{task['taskDescription']} {claimTaskRewardRes['message']} -> {claimTaskRewardRes['data'].get('bonusAmount', '') if claimTaskRewardRes['data'] !=None else ''}")
            else:
                print(f"{tab}{task['taskDescription']} <- {'Wes Cok!' if task['checkStatus'] == task['taskStatus'] else 'Loh Kok??'}")

def recoverSpecialBox(token):
    res = fetch('POST', 'https://api-backend.yescoin.fun/game/recoverSpecialBox', token=token).json()
    getSpecialBoxInfoRes = fetch('GET', 'https://api-backend.yescoin.fun/game/getSpecialBoxInfo', token=token).json()
    coinCount = getSpecialBoxInfoRes['data']['recoveryBox']['specialBoxTotalCount']
    boxStatus = getSpecialBoxInfoRes['data']['recoveryBox']['boxStatus']
    print(f"Recover Box\t: {res['message']} | {coinCount}  <- {boxStatus}")
    time.sleep(10)
    collectSpecialBoxCoinRes = fetch('POST', 'https://api-backend.yescoin.fun/game/collectSpecialBoxCoin', token=token, data={"boxType":2,"coinCount":coinCount}).json()
    collectAmount = collectSpecialBoxCoinRes['data']['collectAmount']
    collectStatus = collectSpecialBoxCoinRes['data']['collectStatus']
    print(f"Collect Box\t: {collectAmount} <- {collectStatus}")

def recoverCoinPool(token):
    res = fetch('POST', 'https://api-backend.yescoin.fun/game/recoverCoinPool', token=token).json()
    getGameInfoRes = fetch('GET', 'https://api-backend.yescoin.fun/game/getGameInfo', token=token).json()
    coinPoolLeftCount = getGameInfoRes['data']['coinPoolLeftCount']
    singleCoinValue = getGameInfoRes['data']['singleCoinValue']
    print(f"Recover Coin\t: {res['message']} | coinPoolLeftCount: {coinPoolLeftCount} & singleCoinValue: {singleCoinValue}")
    collectCoin(token)

def collectCoin(token):
    getGameInfoRes = fetch('GET', 'https://api-backend.yescoin.fun/game/getGameInfo', token=token).json()
    coinPoolLeftCount = getGameInfoRes['data']['coinPoolLeftCount']
    print(f"Coin Pool\t: {coinPoolLeftCount}")
    singleCoinValue = getGameInfoRes['data']['singleCoinValue']
    while coinPoolLeftCount > singleCoinValue*10:
        randomHit = random.randrange(singleCoinValue, coinPoolLeftCount//singleCoinValue, singleCoinValue)
        getGameInfoRes = fetch('GET', 'https://api-backend.yescoin.fun/game/getGameInfo', token=token).json()
        coinPoolLeftCount = getGameInfoRes['data']['coinPoolLeftCount']
        singleCoinValue = getGameInfoRes['data']['singleCoinValue']
        collect = fetch('POST', 'https://api-backend.yescoin.fun/game/collectCoin', token=token, data=randomHit).json()
        if collect['message'] != 'Success':
            # print(collect)
            break
        print(f"Collect Coin\t: {collect['message']} | {collect['data']['collectAmount']}/{coinPoolLeftCount} <- {collect['data']['collectStatus']}")
        time.sleep(5)

def getDailyMission(token):
    res = fetch('GET', 'https://api-backend.yescoin.fun/mission/getDailyMission', token=token).json()
    print(f"Daily Mission\t:")
    data = []
    for index, datanya in enumerate(res['data']):
        filtered = {
            'missionStatus' : datanya['missionStatus'],
            'missionId' : datanya['missionId'],
            'name' : datanya['name']
        }
        if datanya['missionStatus'] != 1:
            data.append(filtered)
    checkDailyMission_And_Claim(token, data)

def checkDailyMission_And_Claim(token, data):
    for index, datanya in enumerate(data):
        if datanya['missionStatus'] == 0:
            if datanya['name'] == 'Daily Check-in':
                pass
                # signListRes = fetch('GET', 'https://api-backend.yescoin.fun/signIn/list', token=token).json()
                # idSign = None
                # hariKe = None
                # for item in signListRes['data']:
                #     if item["checkIn"] == 0:
                #         idSign = item["id"]
                #         hariKe = item["name"]
                #         break
                
                # walletRes = fetch('GET', 'https://api-backend.yescoin.fun/wallet/getWallet', token=token).json()
                # wallet = walletRes['data'][0]['friendlyAddress']
                # waktu = str(int(time.time()))
                
                # data = {"id":idSign, "createAt":waktu, "signInType":1, "destination": wallet}
                # signClaim = fetch('POST', 'https://api-backend.yescoin.fun/signIn/claim', token=token, data=data).json()
                # print(f"{index}. {datanya['name']} {hariKe} | Status {datanya['missionStatus']} {signClaim['message']} | {signClaim['data'].get('reward', None) if signClaim['data'] != None else 'Tunggu Besok Cok!'}")
                # claimRewardres = fetch('POST', 'https://api-backend.yescoin.fun/mission/claimReward', token=token, data=datanya['missionId']).json()
                # print(f"{index}. {datanya['name']} | Status {datanya['missionStatus']} {claimRewardres['message']} | {claimRewardres['data'].get('reward', '') if claimRewardres['data'] != None else ''}")
            elif datanya['name'] == 'Use Full Recovery 1 time':
                recoverCoinPool(token)
                claimRewardres = fetch('POST', 'https://api-backend.yescoin.fun/mission/claimReward', token=token, data=datanya['missionId']).json()
                print(f"{index}. {datanya['name']} | Status {datanya['missionStatus']} {claimRewardres['message']} | {claimRewardres['data'].get('reward', '') if claimRewardres['data'] != None else ''}")
            else:
                for _ in range(2):
                    checkDailyMissionRes = fetch('POST', 'https://api-backend.yescoin.fun/mission/checkDailyMission', token=token, data=datanya['missionId']).json()
                    time.sleep(2)
                print(f"{index}. {datanya['name']} | Status {datanya['missionStatus']} {checkDailyMissionRes['message']}", end='\r', flush=True)
                claimRewardres = fetch('POST', 'https://api-backend.yescoin.fun/mission/claimReward', token=token, data=datanya['missionId']).json()
                print(f"{index}. {datanya['name']} | Status {datanya['missionStatus']} {claimRewardres['message']} | {claimRewardres['data'].get('reward', '') if claimRewardres['data'] != None else ''}")
        else:
            print(f"{index}. {datanya['name']} | {'Wes Cok!' if datanya['missionStatus']==1 else ''}")

def claimOfflineBonus(token):   #MASIH BELUM FIX, MASALAH SIGNATURE
    getOfflineInfoRes = fetch('GET', 'https://api-backend.yescoin.fun/game/getOfflineYesPacBonusInfo', token=token).json()
    pesan = getOfflineInfoRes.get('message')
    transactionId = None
    walletRes = fetch('GET', 'https://api-backend.yescoin.fun/wallet/getWallet', token=token).json()
    wallet = walletRes['data'][0]['friendlyAddress']
    print(f"Wallet\t\t: {wallet}")
    
    if pesan != 'offline time not enough':
        isItCanClaim = getOfflineInfoRes['data'][0]['collectStatus']
        transactionId = getOfflineInfoRes['data'][0]['transactionId']
        print(f"Offline Amount\t: {getOfflineInfoRes['data'][0]['collectAmount']} {isItCanClaim}")
        waktu = str(int(time.time()))
        data = {
            'id': transactionId,
            'createAt': waktu,
            'claimType': 1,
            'destination': ''}
        print(data)
        signature = hashlib.md5(token.encode()).hexdigest()
        print(signature)
        # res = fetch('POST', 'https://api-backend.yescoin.fun/game/claimOfflineBonus', token=token, data=data, sign=secrets.token_hex(16), tm=waktu).json()
        res = fetch('POST', 'https://api-backend.yescoin.fun/game/claimOfflineBonus', token=token, data=data, sign=signature, tm=waktu).json()
        print(res)
    else:
        print(f"Offline Amount\t: {pesan}")

def main():
    queries = readQuery()
    for index, query in enumerate(queries):
        sub = json.loads(urllib.parse.unquote(urllib.parse.parse_qs(query)['user'][0]))
        username = sub['username']
        print(f"=== [ Akun {index+1} | {username}] ===")
        token = login(query)
        getAccountInfo(token)
        getFinishTaskBonusInfo(token)
        getAccountBuildInfo(token)
        collectCoin(token)
        getDailyMission(token)
        getTaskList(token)
        getFinishTaskBonusInfo(token)
        

if __name__ == '__main__':
    main()