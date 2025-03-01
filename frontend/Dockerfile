# frontend/Dockerfile
FROM node:14

# 設置工作目錄
WORKDIR /app

# 複製 package.json 和 package-lock.json
COPY package*.json ./

# 安裝依賴
RUN npm install

# 複製當前目錄的內容到容器中的 /app 目錄
COPY . .
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=${REACT_APP_API_URL}
# 編譯應用程式
RUN npm run build

# 安裝 serve 套件來提供靜態文件
RUN npm install -g serve

# 暴露應用程序運行的端口（假設是3000）
EXPOSE 3000

# 設置容器啟動時運行的命令
CMD ["serve", "-s", "build"]    