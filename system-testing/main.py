import json
import os
import time
import unittest
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import requests
import threading
import subprocess


class VideoAppTest(unittest.TestCase):
    # 目標URL
    BASE_URL = "http://localhost:3000"

    def setUp(self):
        # 初始化瀏覽器
        options = uc.ChromeOptions()
        options.add_argument("--window-size=1920,1080")
        options.add_experimental_option("prefs", {
            "profile.password_manager_enabled": False, "credentials_enable_service": False}
        )#關閉儲存密碼
        options.add_argument("--disable-notifications")

        self.driver = uc.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 5)  # 5秒等待超時

        # 讀取配置文件
        try:
            with open('config.json', 'r', encoding='utf-8') as config_file:
                self.config = json.load(config_file)
            print("成功載入config文件")
        except FileNotFoundError:
            print("警告: 找不到config.json，將創建基本配置")
            self.config = {
                "video_path": "",
                "test_file_path": "",
                "frontend_service_path": ""
            }
            # 創建基本配置文件
            self._create_default_config()
        except json.JSONDecodeError:
            print("警告: 配置文件格式錯誤，將創建基本配置")
            self.config = {
                "video_path": "",
                "test_file_path": "",
                "frontend_service_path": ""
            }
            self._create_default_config()

    def tearDown(self):
        # 測試完成後關閉瀏覽器
        if self.driver:
            self.driver.quit()

    def _create_default_config(self):
        """創建默認配置文件"""
        try:
            with open('config.json', 'w', encoding='utf-8') as config_file:
                json.dump({
                    "video_path": "./test.mp4",
                    "test_file_path": "./test.txt",
                    "frontend_service_path": "../frontend"
                }, config_file, ensure_ascii=False, indent=4)
            print("已創預設的 config.json")
        except Exception as e:
            print(f"無法創建config.json: {str(e)}")

    # TC-001: 成功進入 http://localhost:3000
    def test_001_open_website(self):
        """測試網站進入http://localhost:3000"""
        print("Start Testing TC-001:")

        # 進入BaseURL
        self.driver.get(self.BASE_URL)

        # 驗證是否成功進入（檢查登入頁面元素是否存在）
        try:
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "login-title")))
            print("Testing Pass")
            return True
        except TimeoutException:
            self.fail("Testing Fail")
            return False

    # TC-002: 伺服器未啟動時嘗試進入網站
    def test_002_server_not_running(self):
        """测试Server為關閉時的錯誤處理"""
        print("Start Testing TC-002")

        #關閉Port 3000
        stop_thread = self.stop_service(3000)

        # 嘗試進入URL
        if str(requests.get(self.BASE_URL)=='<Response [404]>'):
            print('404 Not found')
            print("Testing Pass")
        else:
            print("Testing Fail")

        # 重新開啟Port 3000
        frontend_path = self.config.get("frontend_service_path", "")
        start_thread = self.start_service(frontend_path)
    # TC-003: 訪問不存在的路徑
    def test_003_access_invalid_path(self):
        """測試訪問不存在的路徑"""
        print("Start Testing TC-003")

        # 設定不存在的路徑
        invalid_page = f"{self.BASE_URL}/invalid-page"

        # 嘗試進入URL
        if str(requests.get(invalid_page) == '<Response [404]>'):
            print('404 Not found')
            print("Testing Pass")
        else:
            print("Testing Fail")

    # TC-004: 使用正確帳號密碼註冊與登入
    def test_004_login_with_valid_credentials(self):
        """測試使用有效的帳號密碼登入"""
        print("Start Testing TC-004")

        # 註冊的帳號密碼
        email = "testForSystemTest@example.com"
        password = "Test@123456ForSystemTest"
        username = "TEST_USER_ForSystemTest"

        # 先進行註冊
        self._register_user(username, email, password)

        # 登入
        success = self._login(email, password)

        if success:
            print("Testing Pass")
            return True
        else:
            self.fail("Testing Fail")
            return False

    # TC-005: 使用錯誤帳號密碼登入
    def test_005_login_with_invalid_credentials(self):
        """測試使用無效帳號密碼登入"""
        print("Start Testing TC-005")

        # 訪問登入頁面
        self.driver.get(self.BASE_URL)

        # 使用錯誤的帳號密碼登入
        email = "wrong@example.com"
        password = "wrongpassword"

        # 輸入帳號密碼
        self.wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='email']")))
        email_input = self.driver.find_element(By.XPATH, "//input[@type='email']")
        password_input = self.driver.find_element(By.XPATH, "//input[@type='password']")

        email_input.clear()
        email_input.send_keys(email)
        password_input.clear()
        password_input.send_keys(password)

        # 點擊登入按鈕
        login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()

        # 等待錯誤Message
        try:
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "error-message")))
            error_message = self.driver.find_element(By.CLASS_NAME, "error-message").text
            assert "登入失敗" in error_message or "Invalid credentials" in error_message
            print(f"Testing Pass: message - {error_message}")
            return True
        except (TimeoutException, AssertionError):
            self.fail("Testing Fail")
            return False

    # TC-007: 上傳支援的影片格式
    def test_007_upload_supported_video_format(self):
        """測試上傳支援的影片格式"""
        print("Start Testing TC-007")

        # 先登入
        if not self._login("testForSystemTest@example.com", "Test@123456ForSystemTest"):
            self.fail("無法登入，測試中斷")
            return False

        # 點擊上傳影片按鈕
        self.wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(text(), '上傳視頻')]")))
        upload_button = self.driver.find_element(By.XPATH, "//button[contains(text(), '上傳視頻')]")
        upload_button.click()

        # 等待上傳表單出現
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "upload-form")))

        # 填寫標題
        title_input = self.driver.find_element(By.XPATH, "//input[@type='text']")
        title_input.clear()
        title_input.send_keys("測試影片")

        # 從配置文件中讀取影片路徑
        video_path = self.config.get("video_path", "")

        if not video_path or not os.path.exists(video_path):
            print(f"影片路徑無效或不存在: {video_path}")
            print("請在配置文件中設置正確的影片路徑")
            return False

        # 上傳影片檔案
        file_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
        file_input.send_keys(video_path)

        # 點擊上傳按鈕
        submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_button.click()

        # 等待上傳成功並返回到影片列表
        try:
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "video-grid")))
            # 檢查新上傳的影片是否出現在列表中
            video_titles = self.driver.find_elements(By.CLASS_NAME, "video-title")
            uploaded = False
            for title in video_titles:
                if "測試影片" in title.text:
                    uploaded = True
                    break

            assert uploaded, "新上傳的影片未在列表中顯示"
            print("Testing Pass")
            return True
        except (TimeoutException, AssertionError) as e:
            self.fail(f"Testing Fail: {str(e)}")
            return False

    # TC-008: 上傳不支援的影片格式
    def test_008_upload_unsupported_file_format(self):
        """測試上傳不支援的檔案格式"""
        print("Start Testing: TC-008")

        # 先登入
        if not self._login("testForSystemTest@example.com", "Test@123456ForSystemTest"):
            self.fail("無法登入，測試中斷")
            return False

        # 點擊上傳影片按鈕
        self.wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(text(), '上傳視頻')]")))
        upload_button = self.driver.find_element(By.XPATH, "//button[contains(text(), '上傳視頻')]")
        upload_button.click()

        # 等待上傳表單出現
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "upload-form")))

        # 填寫標題
        title_input = self.driver.find_element(By.XPATH, "//input[@type='text']")
        title_input.clear()
        title_input.send_keys("Not_Support_Video")

        # 從配置文件中讀取測試文件路徑
        file_path = self.config.get("test_file_path", "")

        if not file_path or not os.path.exists(file_path):
            print(f"測試文件路徑無效或不存在: {file_path}")
            print("請在配置文件中設置正確的測試文件路徑")
            return False

        # 上傳不支援的檔案
        file_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
        file_input.send_keys(file_path)

        # 點擊上傳按鈕
        submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_button.click()

        # 等待錯誤訊息
        try:
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "error-message")))
            error_message = self.driver.find_element(By.CLASS_NAME, "error-message").text
            print(f"Testing Pass - {error_message}")
            return True
        except TimeoutException:
            self.fail("Testing Fail")
            return False

    # TC-010: 成功播放已上傳的影片
    def test_010_play_uploaded_video(self):
        """測試影片是否能正常播放"""
        print("Start Testing TC-010")

        # 先登入
        if not self._login("testForSystemTest@example.com", "Test@123456ForSystemTest"):
            self.fail("無法登入，測試中斷")
            return False

        # Loading視訊列表
        try:
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "video-card")))
            # 點擊第一個影片播放
            video_element = self.driver.find_element(By.TAG_NAME, "video")
            video_element.click()

            # 等待影片播放
            time.sleep(2)  # 简单等待视频加载

            print("Testing Pass")
            return True
        except TimeoutException:
            print("Testing Fail")
            return False

    # TC-012: 測試影片播放中途暫停與繼續播放
    def test_012_pause_and_resume_video(self):
        """測試暫停與播放功能"""
        print("Start Testing TC-012")

        # 先登入
        if not self._login("testForSystemTest@example.com", "Test@123456ForSystemTest"):
            self.fail("無法登入，測試中斷")
            return False

        # Load影片列表
        try:
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "video-card")))
            # 點擊第一個影片播放
            video_element = self.driver.find_element(By.TAG_NAME, "video")
            video_element.click()

            # 等待影片播放
            time.sleep(2)

            # 暫停播放
            video_element.click()
            time.sleep(1)

            # 繼續播放
            video_element.click()
            time.sleep(1)

            print("Testing Pass")
            return True
        except TimeoutException:
            print("Testing Fail")
            return False

    # TC-013: 成功刪除影片
    def test_013_delete_video(self):
        """測試刪除影片"""
        print("Start Testing TC-013")

        # 先登入
        if not self._login("testForSystemTest@example.com", "Test@123456ForSystemTest"):
            self.fail("無法登入，測試中斷")
            return False

        # 等待影片列表
        try:
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "video-card")))

            # 抓取刪除影片前的數量
            video_cards_before = len(self.driver.find_elements(By.CLASS_NAME, "video-card"))

            if video_cards_before == 0:
                print("Testing Skip: No Video")
                return False

            # 點擊第一個影片刪除按鈕
            delete_button = self.driver.find_element(By.CLASS_NAME, "delete-button")
            delete_button.click()

            # 處理確認對話筐
            self.driver.switch_to.alert.accept()

            # 等待刪除完成
            time.sleep(2)

            # 獲取刪除後的影片列表
            video_cards_after = len(self.driver.find_elements(By.CLASS_NAME, "video-card"))

            # 確認影片是否被刪除
            assert video_cards_after == video_cards_before - 1, "视频未被成功删除"

            print("Testing Pass")
            return True
        except (TimeoutException, AssertionError) as e:
            self.fail(f"Testing Fail: {str(e)}")
            return False

    # TC-014: 刪除後嘗試重新整理頁面
    def test_014_refresh_after_delete(self):
        """測試刪除後刷新頁面，確認影片已經刪除了"""
        print("开始测试 TC-014: 删除后尝试重新整理页面")

        # 先執行刪除
        if not self.test_013_delete_video():
            print("無法執行刪除測試，跳過此測試")
            return False

        # 記錄當前影片數量
        video_cards_before_refresh = len(self.driver.find_elements(By.CLASS_NAME, "video-card"))

        # 刷新頁面
        self.driver.refresh()

        # 等待頁面重新刷新
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "navbar")))
        time.sleep(1)

        # 檢查影片列表跟刪除前的變化
        video_cards_after_refresh = len(self.driver.find_elements(By.CLASS_NAME, "video-card"))

        assert video_cards_after_refresh == video_cards_before_refresh, "刷新頁面發現影片列表發生變化"

        print("Testing Pass")
        return True

    # TC-016: 成功登出
    def test_016_logout(self):
        """测试登出功能"""
        print("Start Testing TC-016")

        # 先登入
        if not self._login("testForSystemTest@example.com", "Test@123456ForSystemTest"):
            self.fail("無法登入，測試中斷")
            return False

        # 點擊登出按鈕
        self.wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(text(), '登出')]")))
        logout_button = self.driver.find_element(By.XPATH, "//button[contains(text(), '登出')]")
        logout_button.click()

        # 確認是否回到登入的頁面了
        try:
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "login-title")))
            print("Testing Pass")
            return True
        except TimeoutException:
            self.fail("Testing Fail")
            return False

    # TC-017: 登出後嘗試使用瀏覽器「返回」功能
    def test_017_back_after_logout(self):
        """測試登出後，使用返回功能"""
        print("Start Testing TC-017")

        # 先登入
        if not self._login("testForSystemTest@example.com", "Test@123456ForSystemTest"):
            self.fail("無法登入，測試中斷")
            return False

        # 確認進入主頁面
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "navbar")))

        # 點擊登出按鈕
        logout_button = self.driver.find_element(By.XPATH, "//button[contains(text(), '登出')]")
        logout_button.click()

        # 確認是否回到登入頁面
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "login-title")))

        # 使用瀏覽器的返回頁面
        self.driver.back()

        # 驗證是否仍在登入頁面(不能進入保護的頁面)
        try:
            time.sleep(1)
            current_url = self.driver.current_url

            # 檢查網頁元素是否是在登入頁面
            login_elements = self.driver.find_elements(By.CLASS_NAME, "login-title")
            navbar_elements = self.driver.find_elements(By.CLASS_NAME, "navbar")

            if len(login_elements) > 0 and len(navbar_elements) == 0:
                print("Testing Pass")
                return True
            else:
                self.fail("Testing Fail")
                return False
        except Exception as e:
            self.fail(f"Testing Fail: {str(e)}")
            return False

    # TC-018: 未登入的使用者進入保護的頁面
    def test_018_access_protected_page_without_login(self):
        """測試未登入的使用者直接進入保護的頁面"""
        print("Start Testing TC-018")

        # 先進入BASE_URL
        self.driver.get(self.BASE_URL)

        # 嘗試進入影片列表
        self.driver.get(f"{self.BASE_URL}/videos")

        # 等待網頁載入
        time.sleep(2)

        # 確認是否在登入頁面
        try:
            login_elements = self.driver.find_elements(By.CLASS_NAME, "login-title")
            assert len(login_elements) > 0, "未顯示登入頁面"
            print("Testing Pass")
            return True
        except AssertionError:
            self.fail("Testing Fail")
            return False

    # 註冊新用戶
    def _register_user(self, username, email, password):
        """註冊新用戶"""
        # 進入BASE_URL
        self.driver.get(self.BASE_URL)

        # 點擊創立新用戶
        try:
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '創建帳號')]")))
            create_account_button = self.driver.find_element(By.XPATH, "//button[contains(text(), '創建帳號')]")
            create_account_button.click()

            # 填寫使用者資訊
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), '創建新帳號')]")))

            username_input = self.driver.find_element(By.XPATH, "//label[text()='使用者名稱']/following-sibling::input")
            email_input = self.driver.find_element(By.XPATH, "//label[text()='電子郵件']/following-sibling::input")
            password_input = self.driver.find_element(By.XPATH, "//label[text()='密碼']/following-sibling::input")
            confirm_password_input = self.driver.find_element(By.XPATH,
                                                              "//label[text()='確認密碼']/following-sibling::input")

            username_input.clear()
            username_input.send_keys(username)
            email_input.clear()
            email_input.send_keys(email)
            password_input.clear()
            password_input.send_keys(password)
            confirm_password_input.clear()
            confirm_password_input.send_keys(password)

            # 送出使用者資訊
            register_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            register_button.click()

            # 等待成功與失敗的message
            try:
                self.wait.until(lambda d: d.find_element(By.CLASS_NAME, "success-message").is_displayed() or
                                          d.find_element(By.CLASS_NAME, "error-message").is_displayed())

                # 檢查成功註冊的message
                success_elements = self.driver.find_elements(By.CLASS_NAME, "success-message")
                error_elements = self.driver.find_elements(By.CLASS_NAME, "error-message")

                if len(success_elements) > 0:
                    print(f"註冊成功: {success_elements[0].text}")
                    time.sleep(2)
                    return True
                elif len(error_elements) > 0 and "已註冊" in error_elements[0].text:
                    # 帳號已存在
                    print(f"帳號已存在: {error_elements[0].text}")
                    # 返回登录页面
                    login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), '登入')]")
                    login_button.click()
                    return True
                else:
                    print(f"註冊失敗: {error_elements[0].text if len(error_elements) > 0 else '未知错误'}")
                    return False
            except TimeoutException:
                print("註冊超時")
                return False
        except Exception as e:
            print(f"註冊錯誤: {str(e)}")
            return False

    # 登入帳號
    def _login(self, email, password):
        """登入使用者"""
        # 進入BASE_URL
        self.driver.get(self.BASE_URL)

        # 等待頁面加載
        try:
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "login-title")))

            # 輸入使用者資訊
            email_input = self.driver.find_element(By.XPATH, "//input[@type='email']")
            password_input = self.driver.find_element(By.XPATH, "//input[@type='password']")

            email_input.clear()
            email_input.send_keys(email)
            password_input.clear()
            password_input.send_keys(password)

            # 點擊登入按鈕
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()

            # 等待登入，確認是否進入首頁
            try:
                self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "navbar")))
                return True
            except TimeoutException:
                # 檢查是否有錯誤消息
                error_elements = self.driver.find_elements(By.CLASS_NAME, "error-message")
                if len(error_elements) > 0:
                    print(f"登入失敗: {error_elements[0].text}")
                else:
                    print("登入失敗: 未知錯誤")
                return False
        except Exception as e:
            print(f"登入過程中失敗: {str(e)}")
            return False

    # 呼叫外部function
    def call_service_manager(self,command, target=None):
        def thread_function():
            cmd = ['python', 'service_manager.py', command]

            if target is not None:
                cmd.append(str(target))

            print(f"執行: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            stdout, stderr = process.communicate()

            if process.returncode == 0:
                print(f"執行成功: {' '.join(cmd)}")
                print(f"輸出: {stdout.decode('utf-8')}")
            else:
                print(f"執行失敗: {' '.join(cmd)}")
                print(f"錯誤: {stderr.decode('utf-8')}")

        thread = threading.Thread(target=thread_function)
        thread.start()
        return thread

    # 使用示例
    def stop_service(self,port):
        return self.call_service_manager('stop', port)

    def start_service(self,project_path):
        return self.call_service_manager('start', project_path)


if __name__ == "__main__":
    # 測試單個測試案例
    test = VideoAppTest()
    test.setUp()
    test.test_002_server_not_running()
    test.tearDown()

    # 測試所有測試案例
    #unittest.main()