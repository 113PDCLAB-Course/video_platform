FROM python:3.12

# 設置工作目錄
WORKDIR /app
RUN mkdir /app/uploads

# 複製 requirements.txt 到容器中
COPY requirements.txt .
ARG MONGODB_HOST
ENV MONGODB_HOST=${MONGODB_HOST}
# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製當前目錄的內容到容器中的 /app 目錄
COPY . .

# 暴露應用程序運行的端口（假設是8000）
EXPOSE 8080
# 設置容器啟動時運行的命令（根據您的應用程序調整）
CMD ["python", "main.py"]