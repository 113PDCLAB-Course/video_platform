1. cd backend

2. python3 -m venv venv

3. # Windows:
	venv\Scripts\activate
   # Linux/Mac:
	source venv/bin/activate

4. pip3 install requirements.txt

5. 安裝MongoDB community

6.  #Windows
	mongod --dbpath /data/db
    #MacOS
	mongod --dbpath /usr/local/var/mongodb

7. python3 main.py

8. cd ../

9. cd frontend

10. 安裝node.js

11. npx create-react-app .

12. npm install

13. npm start

會自動開啟瀏覽器localhost:3000

測試方式：
#POSTMAN:

1. 註冊使用者：
方法：POST
URL：http://localhost:8080/api/register
Headers：
- Content-Type: application/json
Body (raw JSON)：
{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpassword"
}

2. 用戶登入
方法：POST
URL：http://localhost:8080/api/login
Headers：
- Content-Type: application/json
Body (raw JSON)：
{
    "email": "test@example.com",
    "password": "testpassword"
}

3. 上傳視頻
方法：POST
URL：http://localhost:8080/api/videos
Headers：
- Authorization: Bearer YOUR_ACCESS_TOKEN
Body (form-data)：
- title: 您的視頻標題
- file: 選擇視頻文件

4. 獲取視頻列表
方法：GET
URL：http://localhost:8080/api/videos
Headers：
- Authorization: Bearer YOUR_ACCESS_TOKEN
