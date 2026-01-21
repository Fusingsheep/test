# 使用微软官方 Playwright 镜像 (包含 Python 环境和浏览器依赖)
FROM mcr.microsoft.com/playwright:v1.41.0-jammy

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装 Python 包
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制你的代码
COPY main.py .

# 暴露端口 (和你的代码一致)
EXPOSE 8000

# 启动命令
# 注意：直接用 uvicorn 启动，生产环境不需要 reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "1234"]