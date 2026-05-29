# DigiKey 產品搜尋腳本

這是一個簡單的 Python 腳本，從 DigiKey 取得臨時 OAuth2 令牌，並使用 DigiKey API 執行關鍵字產品搜尋。

## 系統需求

- Python 3.7+
- `requests`
- `python-dotenv`
- `prettytable`

## 設定

1. 安裝相依套件：

```bash
pip install requests python-dotenv prettytable
```
或是使用 [uv](https://docs.astral.sh/uv/#highlights)：
```bash
uv sync
```

2. 在相同資料夾中建立 `.env` 檔案，內容如下：

```env
CLIENT_ID=your_digikey_client_id
CLIENT_SECRET=your_digikey_client_secret
```

## 使用方式

在專案資料夾中執行腳本：

```bash
python main.py -k "<keywords>" [-l recordLimit] [-o output]
```

### 範例 1：只輸入必填關鍵字（最基礎用法）
```bash
python main.py -k "resistor 10k"
```
### 範例 2：指定只回傳 5 筆紀錄
```bash
python main.py -k "STM32F103" -l 5
```
### 範例 3：輸出為 JSON 檔案
```bash
python main.py -k "STM32F103" -l 5 -o results.json
```
此腳本將會：

- 從 `.env` 載入 API 憑證
- 向 DigiKey 請求 OAuth2 存取令牌
- 使用 DigiKey 產品搜尋 API 執行關鍵字搜尋
- 列印分類名稱、子分類、封裝/外殼和供應商器件封裝資訊

額外說明：
- 腳本會自動從 .env 載入 CLIENT_ID 與 CLIENT_SECRET，並向 DigiKey 交換 OAuth2 存取令牌。
- 預設會在輸出中以表格格式顯示結果；若使用 -o 參數則會把結果寫成 JSON 檔案。
- 請確保 .env 檔案已建立且內容正確。 

## 注意事項

- 目前的搜尋關鍵字可透過 -k 參數傳入。
- 腳本會根據設定的 URL 使用 DigiKey 沙盒或正式環境端點。
