# Python Unit Test 
[repo](https://github.com/113PDCLAB-Course/video_platform)
寫單元測試，主要是針對 `VIDEO_PLATFORM/backend/rest_api.py` 的 function 寫測試，請按照下面測試案例寫測試

 
* `register` 大衛
* `login`, `get_videos` 正文
* `create_video` 家弘
* `delete_video` 英碩
* `increment_views` 學妹

## template 
> 這裡是 template 
> 可以直接往下看
## 測試案例
### 測試案例編號: <functino name 的縮寫>-<number>
* 測試案例名稱: <API NAME> - <通過 or 會出什麼錯> 
* 測試輸入: 傳送 request <API method API name>，<傳送的東西是什麼>。
<視情況需要，在這邊打入 input>
* 預期結果: <貼上 raise 的程式碼> 

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
* 測試輸入:
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
    "username":"example",
    "password":"123456",
    "email":"existing@example.com"
}
```
* 預期結果: `web.HTTPBadRequest(text="Email already registered")`
---

### 測試案例編號: RE-004
* 測試案例名稱: Register API - 註冊成功  
* 測試輸入: 
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
            "id": '67d427d6a754205dd6ab92fb',
            "username": "example",
            "email": "existing@example.com"
        })
```
    
## Create Video -  API 
### 測試目標
驗證 `Create Video` API 在不同輸入下的行為，包括token驗證各種錯誤，影片文件格式錯誤，正常上傳等情況。

## 測試案例
### 測試案例編號: CR-001
* 測試案例名稱: Create Video API - 缺少授權標頭
* 測試輸入:
```json
{
    Header: 無 Authorization 標頭
    Body (form-data)：
    {
        title: "test.mp4",
        file: valid.mp4
    }
}
```
* 預期結果: `web.HTTPUnauthorized(text="Missing or invalid token")`

---
### 測試案例編號: CR-002
* 測試案例名稱: Create Video - 無效授權標題頭測試
* 測試輸入:
```json
{
    Header: Authorization:  <有效Token>
    Body (form-data)：
    {
        title: "test.mp4",
        file: valid.mp4
    }
}
```
* 預期結果: `web.HTTPUnauthorized(text="Missing or invalid token")`

---
### 測試案例編號: CR-003
* 測試案例名稱: Create Video API - 無效的Token錯誤測試
* 測試輸入:
```json
{
    Header: Authorization: Bearer <無效Token>
    Body (form-data)：
    {
        title: "test.mp4",
        file: valid.mp4
    }
}
```
* 預期結果: `web.HTTPUnauthorized(text="Invalid token")`
---

### 測試案例編號: CR-004
* 測試案例名稱: Create Video API - 上傳影片格式不對
* 測試輸入:
```json
{
    Header: Authorization: Bearer <有效Token>
    Body (form-data)：
    {
        title: "test.mp4",
        file: invalid.mp4
    }
}
```
* 預期結果: `web.HTTPBadRequest(text="No video file provided")`
---

### 測試案例編號: CR-005
* 測試案例名稱: Create Video API - 影片上傳成功  
* 測試輸入: 
```json
{
    Header: Authorization: Bearer <有效Token>
    Body (form-data)：
    {
        title: "test.mp4",
        file: valid.mp4
    }
    
}
```
* 預期結果: 
```python
web.json_response({
                "id": '67d42da7c69a91285466b1db',
                "title": "test.mp4",
                "file_path": "/upload/test.mp4"
            })
```

    
    
    
## Increment Views -  API 
### 測試目標:
驗證 Increment Views API 在不同情境下的行為，包括無效影片 ID 格式、影片存在時的成功更新，以及影片不存在時的錯誤處理

## 測試案例
### 測試案例編號: IV-001
* 測試案例名稱: Increment Views API - 無效影片ID格式測試 
* 測試輸入:
```json
{
    "method": "POST",
    "url": "/api/videos/1234569842/view",
    "headers": {
        "Authorization": "<有效Token>"
    },
    "body": {}
}

```
* 預期結果: `web.HTTPInternalServerError(
    text="'invalid_video_id' is not a valid ObjectId, it must be a 12-byte input or a 24-character hex string"
)`
---
### 測試案例編號: IV-002
* 測試案例名稱: Increment Views API - 影片存在測試
* 測試輸入:
```json
{
    "method": "POST",
    "url": "/api/videos/507f1f77bcf86cd799439012/view",
    "headers": {
        "Authorization": "<有效Token>"
    },
    "body": {}
}

```
* 預期結果: `web.json_response({"message": "View count updated"})
`

---
### 測試案例編號: IV-003
* 測試案例名稱: Increment Views API - 影片不存在測試
* 測試輸入:
```json
{
    "method": "POST",
    "url": "/api/videos/507f1f77bcf86cd799439011/view",
    "headers": {
        "Authorization": "<有效Token>"
    },
    "body": {}
}

```
* 預期結果: `web.HTTPNotFound(text="Video not found")`
---

## Login API 
### 測試目標
驗證 `login` API 在不同輸入下的行為，包括正常登入、缺少必要參數、帳號或密碼不正確等情況。

## 測試案例
### 測試案例編號: LG-001
* 測試案例名稱: Login API - 登入成功  
* 測試輸入:
    ``` json
    {
        "method": "POST",
        "url": "/api/login",
        "body": {
            "email": "example@gmail.com",
            "password": "password"
        }
    }
    ```
* 預期結果: 
    ``` python
    web.json_response({
        "access_token": "valid-token"
    })
    ```
---
    
### 測試案例編號: LG-002
* 測試案例名稱: Login API - 登入失敗，參數缺少
* 測試輸入:
    ``` json
    {
        "method": "POST",
        "url": "/api/login",
        "body": {
            "email": "example@gmail.com"
        }
    }
    ```
* 預期結果: 
    ``` python
    web.HTTPUnauthorized(text="Invalid credentials")
    ```
---
    
### 測試案例編號: LG-003
* 測試案例名稱: Login API - 登入失敗，帳號或密碼錯誤
* 測試輸入:
    ``` json
    {
        "method": "POST",
        "url": "/api/login",
        "body": {
            "email": "invalid-example@gmail.com",
            "password": "invalid-password"
        }
    }
    ```
* 預期結果: 
    ``` python
    web.HTTPUnauthorized(text="Invalid credentials")
    ```
---
    

## Get Videos API 
### 測試目標
驗證 Get Videos API 在不同輸入下的行為，包括正常獲取影片列表、獲取空影片列表、影片資料異常等情況。

## 測試案例
### 測試案例編號: GV-001
* 測試案例名稱: Get Videos API - 成功獲取影片列表
* 測試輸入:
    ``` json
    {
        "method": "GET",
        "url": "/api/videos",
        "headers": {
            "Authorization": "<有效Token>"
        }
    }
    ```
- 測試前置條件:
    1. 資料庫中有多筆影片資料。
    2. 每部影片有 `uploader_id`，且部分 `uploader_id` 為有效 `ObjectId`，部分為 `"default_user_id"` 或無效 ID。

* 預期結果: 
   1. 回傳 JSON 陣列，每個元素包含 `id`, `title`, `description`, `file_path`, `uploader`, `views`。 
        ``` json
        [
            {
                "id": "67d42da7c69a91285466b1db",
                "title": "test.mp4",
                "description": "test video",
                "file_path": "/upload/test.mp4",
                "uploader": "root",
                "views": 1
            },
            {
                "id": "67d42da7c69a91285466b1dc",
                "title": "test2.mp4",
                "description": "test video2",
                "file_path": "/upload/test2.mp4",
                "uploader": "Unknown",
                "views": 2
            }
        ]
        ```
2. `uploader` 欄位:
    - 若 `uploader_id` 有對應使用者，則顯示該使用者的 `username`。
    - 若 `uploader_id` 為 "default_user_id" 或查無對應使用者，則顯示 `"Unknown"`。
---
    
### 測試案例編號: GV-002
* 測試案例名稱: Get Videos API - 成功獲取空影片列表
* 測試輸入:
    ``` json
    {
        "method": "GET",
        "url": "/api/videos",
        "headers": {
            "Authorization": "<有效Token>"
        }
    }
    ```
- 測試前置條件:
    資料庫中的 videos 集合為空。
* 預期結果: 
    ``` json
    []
    ```
---
    
### 測試案例編號: GV-003
* 測試案例名稱: Get Videos API - 影片資料欄位異常處理測試
* 測試輸入:
    ``` json
    {
        "method": "GET",
        "url": "/api/videos",
        "headers": {
            "Authorization": "<有效Token>"
        }
    }
    ```
- 測試前置條件:
    videos 集合內部分影片資料缺少必要欄位，例如 `_id`, `title`, `file_path`, `views`。
* 預期結果: 
1. 略過有錯誤的影片，正常返回其他可用的影片資料。
    ``` json
    [
        {
            "id": "67d42da7c69a91285466b1db",
            "title": "test.mp4",
            "description": "test video",
            "file_path": "/upload/test.mp4",
            "uploader": "root",
            "views": 1
        }    
    ]
    ```
    
2. 在伺服器端記錄錯誤資訊。
    ```python
    print(f"Error processing video {video.get('_id')}: {str(e)}")
    ```

---
    

## Delete Video - API 
### 測試目標
驗證 `Delete Video` API 在不同輸入下的行為，包括無效的身份驗證 Token、提供無效視頻ID格式、視頻不存在、視頻刪除失敗但數據庫仍正常刪除記錄，以及成功刪除視頻的情況。

## 測試案例
### 測試案例編號: DV-001
* 測試案例名稱: Delete Video API - 驗證身份錯誤測試  
* 測試輸入:
    ``` json
    {
        "method": "DELETE",
        "url": "/api/videos/67d52d4bb676629c4b3b7c96",
        "headers": {
            "Authorization": "<無效Token>"
        }
        "body": {}
    }
    ```
* 預期結果: 
    ``` 
    web.HTTPUnauthorized(text="Missing or invalid token")
    ```
---
### 測試案例編號: DV-002
* 測試案例名稱: Delete Video API – 無效視頻ID格式測試  
* 測試輸入:
    ``` json
    {
        "method": "DELETE",
        "url": "/api/videos/1234567",
        "headers": {
            "Authorization": "Bearer"+"<有效Token>"
        }
        "body": {}
    }
    ```
* 預期結果: 
    ``` 
    web.HTTPBadRequest(text="Invalid video ID format")
    ```
---
### 測試案例編號: DV-003
* 測試案例名稱: Delete Video API – 有效視頻ID但影片不存在資料庫測試  
* 測試輸入:
    ``` json
    {
        "method": "DELETE",
        "url": "/api/videos/67d52d4bb676629c4b3b7c97",
        "headers": {
            "Authorization": "Bearer"+"<有效Token>"
        }
        "body": {}
    }
    ```
* 預期結果: 
    ``` 
    web.HTTPNotFound(text="Video not found")
    ```
---
### 測試案例編號: DV-004
* 測試案例名稱: Delete Video API – 資料庫紀錄刪除錯誤測試  
* 測試輸入:
    ``` json
    {
        "method": "DELETE",
        "url": "/api/videos/67d5471fb676629c4b3b7ca2",
        "headers": {
            "Authorization": "Bearer"+"<有效Token>"
        }
        "body": {}
    }
    ```
* 預期結果: 
    ``` 
    raise web.HTTPNotFound(text="Video not found or already deleted")
    ```
---
### 測試案例編號: DV-005
* 測試案例名稱: Delete Video API – 視頻成功刪除測試  
* 測試輸入:
    ``` json
    {
        "method": "DELETE",
        "url": "/api/videos/67d52d4bb676629c4b3b7c96",
        "headers": {
            "Authorization": "Bearer"+"<有效Token>"
        }
        "body": {}
    }
    ```
* 預期結果: 
    ``` 
    web.json_response({
    "message": "Video deleted successfully",
    "video_id": "67d52d4bb676629c4b3b7c96"
    })

    ```