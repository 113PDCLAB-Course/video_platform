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
import sys
import io
from contextlib import redirect_stdout, redirect_stderr

# 導入 xmlrunner (請確保已安裝)
import xmlrunner


class VideoAppTest(unittest.TestCase):
    # 目標URL
    BASE_URL = "http://localhost:3000"

    def setUp(self):
        # 初始化瀏覽器
        options = uc.ChromeOptions()
        options.add_argument("--window-size=1920,1080")
        options.add_experimental_option("prefs", {
            "profile.password_manager_enabled": False, "credentials_enable_service": False}
                                        )  # 關閉儲存密碼
        options.add_argument("--disable-notifications")

        self.driver = uc.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 5)  # 5秒等待超時

        # 讀取配置文件
        try:
            with open('config.json', 'r', encoding='utf-8') as config_file:
                self.config = json.load(config_file)
        except FileNotFoundError:
            self.config = {
                "video_path": "",
                "test_file_path": "",
                "frontend_service_path": ""
            }
            # 創建基本配置文件
            self._create_default_config()
        except json.JSONDecodeError:
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
        except Exception as e:
            pass

    # TC-001: 成功進入 http://localhost:3000
    def test_001_open_website(self):
        """測試網站進入http://localhost:3000"""
        # 進入BaseURL
        self.driver.get(self.BASE_URL)

        # 驗證是否成功進入（檢查登入頁面元素是否存在）
        try:
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "login-title")))
            return True
        except TimeoutException:
            self.fail("無法正確進入網站")
            return False

    # TC-002: 伺服器未啟動時嘗試進入網站
    def test_002_server_not_running(self):
        """测试Server為關閉時的錯誤處理"""
        # 關閉Port 3000
        stop_thread = self.stop_service(3000)

        # 嘗試進入URL
        response = requests.get(self.BASE_URL)
        if response.status_code == 404:
            pass
        else:
            self.fail(f"Expected 404 response, but got {response.status_code}")

        # 重新開啟Port 3000
        frontend_path = self.config.get("frontend_service_path", "")
        start_thread = self.start_service(frontend_path)

    # TC-003: 訪問不存在的路徑
    def test_003_access_invalid_path(self):
        """測試訪問不存在的路徑"""
        # 設定不存在的路徑
        invalid_page = f"{self.BASE_URL}/invalid-page"

        # 嘗試進入URL
        response = requests.get(invalid_page)
        if response.status_code == 404:
            pass
        else:
            self.fail(f"Expected 404 response, but got {response.status_code}")

    # TC-004: 使用正確帳號密碼註冊與登入
    def test_004_login_with_valid_credentials(self):
        """測試使用有效的帳號密碼登入"""
        # 註冊的帳號密碼
        email = "testForSystemTest@example.com"
        password = "Test@123456ForSystemTest"
        username = "TEST_USER_ForSystemTest"

        # 先進行註冊
        registration_success = self._register_user(username, email, password)

        if not registration_success:
            self.fail("註冊失敗，無法繼續登入測試")
            return

        # 登入
        success = self._login(email, password)

        if not success:
            self.fail("使用有效憑證登入失敗")

    # TC-005: 使用錯誤帳號密碼登入
    def test_005_login_with_invalid_credentials(self):
        """測試使用無效帳號密碼登入"""
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
            return True
        except (TimeoutException, AssertionError):
            self.fail("登入失敗訊息未出現或不符合預期")
            return False

    # TC-007: 上傳支援的影片格式
    def test_007_upload_supported_video_format(self):
        """測試上傳支援的影片格式"""
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
            self.fail(f"影片路徑無效或不存在: {video_path}")
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
            return True
        except (TimeoutException, AssertionError) as e:
            self.fail(f"影片上傳失敗: {str(e)}")
            return False

    # TC-008: 上傳不支援的影片格式
    def test_008_upload_unsupported_file_format(self):
        """測試上傳不支援的檔案格式"""
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
            self.fail(f"測試文件路徑無效或不存在: {file_path}")
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
            return True
        except TimeoutException:
            self.fail("錯誤訊息未出現")
            return False

    # TC-010: 成功播放已上傳的影片
    def test_010_play_uploaded_video(self):
        """測試影片是否能正常播放"""
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

            return True
        except TimeoutException:
            self.fail("找不到影片元素")
            return False

    # TC-012: 測試影片播放中途暫停與繼續播放
    def test_012_pause_and_resume_video(self):
        """測試暫停與播放功能"""
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

            return True
        except TimeoutException:
            self.fail("找不到影片元素")
            return False

    # TC-013: 成功刪除影片
    def test_013_delete_video(self):
        """測試刪除影片"""
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
                self.skipTest("無可刪除的影片")
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
            assert video_cards_after == video_cards_before - 1, "影片未被成功刪除"

            return True
        except (TimeoutException, AssertionError) as e:
            self.fail(f"刪除影片失敗: {str(e)}")
            return False

    # TC-014: 刪除後嘗試重新整理頁面
    def test_014_refresh_after_delete(self):
        """測試刪除後刷新頁面，確認影片已經刪除了"""
        # 先執行刪除
        try:
            self.test_013_delete_video()
        except unittest.SkipTest:
            self.skipTest("無可刪除的影片")
            return

        # 記錄當前影片數量
        video_cards_before_refresh = len(self.driver.find_elements(By.CLASS_NAME, "video-card"))

        # 刷新頁面
        self.driver.refresh()

        # 等待頁面重新刷新
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "navbar")))
        time.sleep(1)

        # 檢查影片列表跟刪除前的變化
        video_cards_after_refresh = len(self.driver.find_elements(By.CLASS_NAME, "video-card"))

        assert video_cards_after_refresh == video_cards_before_refresh, "刷新頁面後影片列表發生變化"

    # TC-016: 成功登出
    def test_016_logout(self):
        """测试登出功能"""
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
            return True
        except TimeoutException:
            self.fail("登出後未返回登入頁面")
            return False

    # TC-017: 登出後嘗試使用瀏覽器「返回」功能
    def test_017_back_after_logout(self):
        """測試登出後，使用返回功能"""
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

            self.assertTrue(len(login_elements) > 0 and len(navbar_elements) == 0,
                            "返回按鈕不當允許訪問登出後的受保護頁面")
            return True
        except Exception as e:
            self.fail(f"測試失敗: {str(e)}")
            return False

    # TC-018: 未登入的使用者進入保護的頁面
    def test_018_access_protected_page_without_login(self):
        """測試未登入的使用者直接進入保護的頁面"""
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
            return True
        except AssertionError:
            self.fail("未重定向至登入頁面")
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
                    time.sleep(2)
                    return True
                elif len(error_elements) > 0 and "已註冊" in error_elements[0].text:
                    # 帳號已存在
                    # 返回登录页面
                    login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), '登入')]")
                    login_button.click()
                    return True
                else:
                    return False
            except TimeoutException:
                return False
        except Exception as e:
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
                return False
        except Exception as e:
            return False

    # 呼叫外部function
    def call_service_manager(self, command, target=None):
        def thread_function():
            cmd = ['python3', 'service_manager.py', command]

            if target is not None:
                cmd.append(str(target))

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            stdout, stderr = process.communicate()

        thread = threading.Thread(target=thread_function)
        thread.start()
        return thread

    def stop_service(self, port):
        return self.call_service_manager('stop', port)

    def start_service(self, project_path):
        return self.call_service_manager('start', project_path)


if __name__ == "__main__":
    # 設置固定參數
    VideoAppTest.BASE_URL = "http://localhost:3000"

    # 關閉所有日誌輸出
    import warnings

    warnings.filterwarnings("ignore")

    # 確保測試報告目錄存在
    report_dir = "jenkins-test-reports"
    os.makedirs(report_dir, exist_ok=True)

    # 創建測試套件
    test_loader = unittest.TestLoader()
    test_suite = test_loader.loadTestsFromTestCase(VideoAppTest)

    # 使用 XMLTestRunner 運行測試並產生報告 (完全靜默模式)
    with io.StringIO() as buf, redirect_stdout(buf), redirect_stderr(buf):
        xml_runner = xmlrunner.XMLTestRunner(output=report_dir, verbosity=0)
        xml_result = xml_runner.run(test_suite)

    # 保存失敗和錯誤信息
    errors_and_failures = []

    # 收集失敗信息
    for test, error_msg in xml_result.failures:
        test_name = test.id().split('.')[-1]
        error_msg = error_msg.split("\n")[-1] if "\n" in error_msg else error_msg
        errors_and_failures.append((test_name, "失敗", error_msg))

    # 收集錯誤信息
    for test, error_msg in xml_result.errors:
        test_name = test.id().split('.')[-1]

        # 提取最相關的錯誤信息
        if "AssertionError:" in error_msg:
            error_msg = error_msg.split("AssertionError:")[-1].strip()
        elif "Error:" in error_msg:
            error_msg = error_msg.split("Error:")[-1].strip()
        else:
            lines = error_msg.split("\n")
            for line in reversed(lines):
                if line.strip() and not line.startswith(" ") and not line.startswith("Traceback"):
                    error_msg = line.strip()
                    break

        errors_and_failures.append((test_name, "錯誤", error_msg))

    # 只輸出測試結果摘要和錯誤/失敗的測試案例
    print("\n===== 測試結果摘要 =====")
    print(f"總計執行: {xml_result.testsRun} 個測試案例")
    print(f"通過: {xml_result.testsRun - len(xml_result.failures) - len(xml_result.errors)} 個")
    print(f"失敗: {len(xml_result.failures)} 個")
    print(f"錯誤: {len(xml_result.errors)} 個")

    if errors_and_failures:
        print("\n===== 失敗和錯誤的測試案例 =====")
        for test_name, status, msg in errors_and_failures:
            print(f"{test_name}: {status}")
            print(f"  原因: {msg}")

    # 設置退出代碼
    sys.exit(not xml_result.wasSuccessful())