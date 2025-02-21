from fastapi import FastAPI, HTTPException
from youtube_transcript_api import YouTubeTranscriptApi
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller

# 로거 설정
logger = logging.getLogger(__name__)

chromedriver_autoinstaller.install()  # ChromeDriver 자동 설치

app = FastAPI()

def extract_youtube_id(url: str) -> str:
    """YouTube URL에서 영상 ID를 추출하는 함수"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError("유효하지 않은 YouTube URL입니다.")

@app.get("/youtube-transcript")
async def get_youtube_transcript(url: str):
    try:
        video_id = extract_youtube_id(url)
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])
        
        # 자막 텍스트만 추출하여 하나의 문자열로 결합
        full_text = " ".join([entry["text"] for entry in transcript])
        
        return {"text": full_text}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/web-content")
async def get_web_content(url: str):
    driver = None
    try:
        # URL 유효성 검사
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("유효하지 않은 URL입니다.")
        
        # Chrome 옵션 설정
        chrome_options = Options()
        chrome_options.add_argument("disable-gpu")
        chrome_options.add_argument('--headless')  # Headless 모드
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument("--remote-debugging-port=9222")

        # Selenium WebDriver 초기화
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        # 페이지가 완전히 로드될 때까지 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # JavaScript 실행 후 페이지 렌더링을 위한 추가 대기
        driver.implicitly_wait(2)
        
        # 페이지 소스 가져오기
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # 불필요한 태그 제거
        for tag in soup(['script', 'style', 'header', 'footer', 'nav']):
            tag.decompose()
        
        # 텍스트 추출 및 정리
        text = soup.get_text()
        logger.info(f"추출된 전체 텍스트: {text[:500]}...") # 처음 500자만 출력
        
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        logger.info(f"정리된 라인들: {lines[:10]}...") # 처음 10줄만 출력
        
        content = ' '.join(lines)
        
        return {"text": content}
    except Exception as e:
        logger.error(f"오류 발생: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=1818)