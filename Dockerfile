# Dùng base image Python
FROM python:3.11-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Cài đặt các thư viện hệ thống cần thiết (nếu có)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy file requirements trước và cài đặt dependencies để tối ưu build cache
COPY Bend/requirements.txt ./Bend/
RUN pip install --no-cache-dir -r Bend/requirements.txt

# Copy toàn bộ mã nguồn của project vào /app
COPY . .

# Expose port 8000
EXPOSE 8000

# Chạy Uvicorn với app từ app/main_api.py trong root, 
# file này sẽ import FastAPI instance từ Bend/app/main_api.py 
CMD ["uvicorn", "app.main_api:app", "--host", "0.0.0.0", "--port", "8000"]
