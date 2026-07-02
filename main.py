import requests, os, sys, json, re
from dotenv import load_dotenv
from prettytable import PrettyTable

def clean_part_number(user_input: str) -> str:
    """
    清理雜訊
    轉大寫、去前後空格，並移除非英數、連字號(-)、斜線(/)的字元（如空格、底線、特殊符號）。
    """
    if not user_input:
        return ""
    
    # 1. 轉大寫並去掉前後空白
    cleaned = user_input.upper().strip()
    
    # 2. 使用 Regex 移除非主要字元
    # [^A-Z0-9\-\/] 代表「不是 A-Z、0-9、-、/」的字元通通取代為空字串
    cleaned = re.sub(r'[^A-Z0-9\-\/]', '', cleaned)
    
    return cleaned

def split_part_number(cleaned_input: str) -> tuple:
    """
    提取核心型號（為退階搜尋做準備）
    使用 Regex 抓取前 5 到 8 碼作為核心型號，剩下的歸為後綴。
    """
    # 這裡的 Regex 意思是：
    # ^([A-Z0-9\-]{5,8}) -> 匹配開頭 5 到 8 碼的英數或連字號（分組 1）
    # (.*)$             -> 剩下的所有字元（分組 2）
    match = re.match(r'^([A-Z0-9\-]{5,8})(.*)$', cleaned_input)
    
    if match:
        core = match.group(1)
        suffix = match.group(2)
        return core, suffix
    
    return cleaned_input, ""

def search_keyword(keywords, access_token, record_count):
    if len(keywords) > 250:
        print("Keywords length is out of limits")
        exit()
    url = "https://api.digikey.com/products/v4/search/keyword"
    headers = {
        "X-DIGIKEY-Client-Id": os.getenv("CLIENT_ID"),
        "Authorization": f"Bearer {access_token}",  # <-- Added this crucial line!
        "X-DIGIKEY-Locale-Site": "TW",               
        "X-DIGIKEY-Locale-Currency": "USD",  
        "Content-Type": "application/json"
    }

    payload = {
        # "keywords": "YJP1608-R001",
        "keywords": f"{keywords}",
        "limit": record_count
    }

    print(f"Searching \"{keywords}\" on DigiKey...")
    return requests.post(url, json=payload, headers=headers)

def get_childCategory(child, array=None, i=1):
    if array is None:
        array = []
    # print("\tChild Category [" + str(i) + "]: " + (child.get('Name') or "None"))
    array.append((child.get('Name') or "None"))
    i += 1
    if child.get("ChildCategories"):
        get_childCategory(child["ChildCategories"][0], array, i)
    return array

def get_access_token(client_id, client_secret):
    """Fetches a temporary OAuth2 token from DigiKey."""
    token_url = "https://api.digikey.com/v1/oauth2/token"
    token_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    token_headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    response = requests.post(token_url, data=token_data, headers=token_headers)
    
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception(f"Failed to obtain access token: {response.status_code} - {response.text}")

def print_usage():
    print("Usage: python main.py <keywords> [recordLimit] [-o output]")
    print("  -k <keywords>: 搜尋關鍵字，例如 -k \"STPS41H100CGY-TR\"")
    print("  [-l recordLimit]: 可選，回傳的最大筆數，預設為 5")
    print("  [-o output]: 可選，輸出結果為 JSON 檔案")
    print("Example:")
    print("  python main.py -k \"STPS41H100CGY-TR\" -l 10")
    print("  python main.py -k \"STPS41H100CGY-TR\" -l 10 -o results.json")
    print("請先建立 .env 檔並設定 CLIENT_ID 與 CLIENT_SECRET。\n")

def main():

    # print("All arguments:", sys.argv)

    args = sys.argv[1:]
    if len(args) < 1 or any(arg in ("--help", "-h") for arg in args):
        print_usage()
        return

    keywords = None
    record_count = 5
    output_file = None
    idx = 0
    while idx < len(args):
        if args[idx] == "-k":
            if idx + 1 >= len(args):
                print("參數 -k 後沒有引數.")
                print_usage()
                return
            keywords = args[idx + 1]
            idx += 2
        elif args[idx] == "-l":
            if idx + 1 >= len(args):
                print("參數 -l 後沒有引數.")
                print_usage()
                return
            try:
                record_count = int(args[idx + 1])
            except ValueError:
                print("recordLimit 必須是阿拉伯數字.")
                print_usage()
                return
            idx += 2
        elif args[idx] == "-o":
            if idx + 1 >= len(args):
                print("參數 -o 後沒有引數.")
                print_usage()
                return
            output_file = args[idx + 1]
            idx += 2
        else:
            print(f"未知參數: {args[idx]}")
            print_usage()
            return

    if not keywords:
        print("必須指定搜尋關鍵字，請使用 -k <keywords>.")
        print_usage()
        return

    # 1. Load env file into
    load_dotenv()

    # 2. Automatically fetch the temporary bearer token
    print("Fetching access token...")
    try:
        access_token = get_access_token(os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET"))
    except Exception as e:
        print(e)
        return
    
    # 進 API 前先做 Regex 清理
    cleaned_keywords = clean_part_number(keywords)
    if cleaned_keywords != keywords:
        print(f"原始輸入: \"{keywords}\" -> Regex 優化後: \"{cleaned_keywords}\"")

    # 3. Build headers including BOTH the Client ID and the Bearer token
    response  = search_keyword(cleaned_keywords, access_token, record_count)
    
    if response.status_code == 200:
        tmp = response.json()
        count = int(tmp['ProductsCount'])
        
        # ─── 【核心修改：第二步，若精準搜尋為 0 筆，啟動 Regex 退階機制】 ───
        if count == 0:
            print(f"No result(s) found for \"{cleaned_keywords}\" on DigiKey.")
            core, suffix = split_part_number(cleaned_keywords)
            
            # 如果有成功切出後綴，則用核心型號再試一次
            if suffix:
                print(f"啟動退階搜尋機制... 砍掉後綴 \"{suffix}\"，改用核心型號 \"{core}\" 重新搜尋...")
                response = search_keyword(core, access_token, record_count)
                tmp = response.json()
                count = int(tmp['ProductsCount'])
            
            # 如果連核心搜尋都找不到，或者根本沒後綴可切，宣告失敗
            if count == 0:
                print(f"退階搜尋依然查無結果。")
                print("Exit.")
                return
        print(f"Found {count} record" + ("s" if count > 1 else ""))
        table = PrettyTable()
        table.field_names = ["ID","Name", "Category", "Child Categories","Package/Case", "Supplier Device Package"]
        mainList = {}
        for index, products in enumerate(tmp['Products']):
            parameters = products['Parameters']
            tmpList = []
            tmpList.append(index + 1) 
            # 品名
            tmpList.append(products['ManufacturerProductNumber'] or "None")
            # 類別
            tmpList.append(products['Category']['Name'] or "None")
            # 子類別
            if ("ChildCategories" in products['Category']) and (len(products['Category']['ChildCategories']) > 0):
                tmpList.append(get_childCategory(products['Category']['ChildCategories'][0]))
            else:
                tmpList.append("None")
            # 供應商封裝
            tmpList.append(next((item for item in parameters if item['ParameterId'] == 16),{'ValueText': "None"})['ValueText'])
            # 封裝 外殼
            tmpList.append(next((item for item in parameters if item['ParameterId'] == 1291),{'ValueText': "None"})['ValueText'])
            mainList[str(tmpList[0])] = dict(
                {
                    "Name":tmpList[1],
                    "Category":tmpList[2],
                    "Child Categories":tmpList[3],
                    "Supplier Device Package":tmpList[4],
                    "Package/Case":tmpList[5]
                })
            

            table.add_row(tmpList)
        print(table)
        if output_file:
            output_dir = os.path.dirname(output_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(mainList, f, indent=2, ensure_ascii=False)
            print(f"Output written to {output_file}")

    else:
        print(f"Search Failed with status {response.status_code}:")
        print(response.text)

if __name__ == "__main__":
    main()