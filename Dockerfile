# Python 3.12 slim 이미지를 기반으로 사용
FROM python:3.12-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 패키지 설치를 위한 requirements.txt 복사
COPY requirements.txt .

# 시스템 패키지 및 Python 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev curl wget gnupg2 && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get remove -y gcc python3-dev && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 애플리케이션 코드 복사
COPY app.py .

# 포트 설정
EXPOSE 1818

# 애플리케이션 실행
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "1818"] 