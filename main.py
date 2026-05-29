import requests, os, sys, json
from dotenv import load_dotenv
from prettytable import PrettyTable


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
    print("  <keywords>: 搜尋關鍵字，例如 STPS41H100CGY-TR")
    print("  [recordLimit]: 可選，回傳的最大筆數，預設為 5")
    print("  [-o output]: 可選，輸出結果為 JSON 檔案")
    print("Example:")
    print("  python main.py STPS41H100CGY-TR 10")
    print("  python main.py STPS41H100CGY-TR 10 -o results.json")
    print("請先建立 .env 檔並設定 CLIENT_ID 與 CLIENT_SECRET。\n")

def main():

    # print("All arguments:", sys.argv)

    args = sys.argv[1:]
    if len(args) < 1 or any(arg in ("--help", "-h") for arg in args):
        print_usage()
        return

    keywords = args[0]
    record_count = 5
    output_file = None
    idx = 1
    while idx < len(args):
        if args[idx] == "-o":
            if idx + 1 >= len(args):
                print("參數 -o 後沒有引數.")
                print_usage()
                return
            output_file = args[idx + 1]
            idx += 2
        else:
            if record_count != 5:
                print(f"未知參數: {args[idx]}")
                print_usage()
                return
            try:
                record_count = int(args[idx])
            except ValueError:
                print("recordLimit 必須是阿拉伯數字.")
                print_usage()
                return
            idx += 1

    # 1. Load env file into
    load_dotenv()

    # 2. Automatically fetch the temporary bearer token
    print("Fetching access token...")
    try:
        access_token = get_access_token(os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET"))
    except Exception as e:
        print(e)
        return

    # 3. Build headers including BOTH the Client ID and the Bearer token
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
        "keywords": keywords,
        "limit": record_count
    }

    print("Searching DigiKey...")
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        print("Success!")
        # print("Json: " + str(response.json()))
        tmp = response.json()
        table = PrettyTable()
        table.field_names = ["ID","Name", "Category", "Child Categories","Supplier Device Package", "Package / Case"]
        mainList = {}
        for index, products in enumerate(tmp['Products']):
            parameters = products['Parameters']
            tmpList = []
            tmpList.append(index) 
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
                    "Package / Case":tmpList[5]
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