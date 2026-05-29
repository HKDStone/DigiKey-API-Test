import requests, os, sys
from dotenv import load_dotenv

def get_childCategory(child, i=1):
    print("\tChild Category ["+str(i)+"]: " + (child['Name'] or "None"))
    i += 1
    if ("ChildCategories" in child) and (len(child["ChildCategories"]) > 0):
        get_childCategory(child["ChildCategories"][0], i)

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
    print("Usage: python main.py <keywords> [recordLimit]")
    print("  <keywords>: 搜尋關鍵字，例如 STPS41H100CGY-TR")
    print("  [recordLimit]: 可選，回傳的最大筆數，預設為 5")
    print("Example:")
    print("  python main.py STPS41H100CGY-TR 10")
    print("請先建立 .env 檔並設定 CLIENT_ID 與 CLIENT_SECRET。\n")

def main():

    # print("All arguments:", sys.argv)

    args = sys.argv[1:]
    if len(args) < 1 or any(arg in ("--help", "-h") for arg in args):
        print_usage()
        return

    keywords = args[0]
    record_count = 5
    if len(args) > 1:
        try:
            record_count = int(args[1])
        except ValueError:
            print("recordLimit must be an integer.")
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
        for index, products in enumerate(tmp['Products']):
            print("Products ["+str(index)+"]: ")
            parameters = products['Parameters']
            print("\tManufacturerProductNumber: " + products['ManufacturerProductNumber'])
            print("\tCategory Name: " + products['Category']['Name'])
            if ("ChildCategories" in products['Category']) and (len(products['Category']['ChildCategories']) > 0):
                get_childCategory(products['Category']['ChildCategories'][0])
            print("\tPackage / Case: " + next((item for item in parameters if item['ParameterId'] == 16),{'ValueText': "None"})['ValueText'])
            print("\tSupplier Device Package: " + next((item for item in parameters if item['ParameterId'] == 1291),{'ValueText': "None"})['ValueText'])
    else:
        print(f"Search Failed with status {response.status_code}:")
        print(response.text)

if __name__ == "__main__":
    main()