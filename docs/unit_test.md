# Python Unit Test 
## 測試環境
- Python 版本: 3.12.3
- 測試框架: `pytest`, `aiohttp`
- 資料庫: `MongoDB`

## Register API 
### 測試目標
驗證 `register` API 在不同輸入下的行為，包括正常註冊、缺少必要參數、信箱已存在等情況。



## 測試案例
### 測試案例編號: RE-001
* 測試案例名稱: Register API - 參數不正確  
* 測試輸入: 傳送 request `POST /api/register`，但提供的參數格式並不是 json。
* 預期結果: `web.HTTPBadRequest(text="Invalid request data")`
---

### 測試案例編號: RE-002
* 測試案例名稱: Register API - 參數有缺
* 測試輸入
```json
{
    "password":"123456",
    "email":"existing@example.com"
}
```
* 預期結果: `web.HTTPBadRequest(text=f"Missing required fields: username")`
---

### 測試案例編號: RE-003
* 測試案例名稱: Register API - email 已註冊  
* 測試輸入:
```json
{
    "password":"123456",
    "email":"existing@example.com"
}
```
* 預期結果: `web.HTTPBadRequest(text="Email already registered")`
---

### 測試案例編號: RE-003
* 測試案例名稱: Register API - 註冊成功  
* 測試步驟 
```json
{
    "username":"example",
    "password":"123456",
    "email":"existing@example.com"
}
```
* 預期結果: 
```python
web.json_response({
            "id": str(result.inserted_id),
            "username": user.username,
            "email": user.email
        })
```
