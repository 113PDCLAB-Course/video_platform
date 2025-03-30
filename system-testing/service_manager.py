import os
import sys
import subprocess
import signal
import psutil
import time


def find_process_by_port(port):
    """根據端口號查找進程"""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            # 不在process_iter中請求connections，而是在後續對每個進程單獨調用
            connections = proc.connections()
            for conn in connections:
                if conn.laddr.port == port:
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None


def stop_service(port):
    """停止在指定端口運行的服務"""
    process = find_process_by_port(port)

    if process:
        print(f"找到在端口 {port} 運行的進程: {process.name()} (PID: {process.pid})")
        try:
            # 先嘗試正常終止
            process.terminate()
            process.wait(timeout=5)
            print(f"成功停止端口 {port} 的服務")
        except psutil.TimeoutExpired:
            # 如果正常終止失敗，則強制結束
            process.kill()
            print(f"已強制停止端口 {port} 的服務")
    else:
        print(f"在端口 {port} 上沒有找到運行的服務")


def start_service(directory, command="npm start"):
    """在指定目錄啟動服務"""
    try:
        # 檢查目錄是否存在
        if not os.path.isdir(directory):
            print(f"錯誤: 目錄 '{directory}' 不存在")
            return False

        # 切換到指定目錄
        os.chdir(directory)
        print(f"已切換到目錄: {directory}")

        # 啟動服務 (非阻塞模式)
        print(f"正在啟動服務，執行命令: {command}")
        # 使用shell=True允許執行複合命令，使用nohup防止終端關閉導致進程終止
        subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # 給服務一些啟動時間
        time.sleep(2)
        print("服務啟動命令已執行")
        return True

    except Exception as e:
        print(f"啟動服務時發生錯誤: {str(e)}")
        return False


def main():
    if len(sys.argv) < 2:
        print("使用方法:")
        print("停止服務: python service_manager.py stop [port]")
        print("啟動服務: python service_manager.py start [directory]")
        return

    action = sys.argv[1].lower()

    if action == "stop":
        if len(sys.argv) < 3:
            port = 3000  # 預設端口
        else:
            try:
                port = int(sys.argv[2])
            except ValueError:
                print("錯誤: 端口必須是數字")
                return
        stop_service(port)

    elif action == "start":
        if len(sys.argv) < 3:
            print("錯誤: 請提供要啟動服務的目錄")
            return
        directory = sys.argv[2]
        start_service(directory)

    else:
        print(f"未知操作: {action}")
        print("可用操作: start, stop")


if __name__ == "__main__":
    main()