import requests
import google.generativeai as genai

# ==========================================
# 1. 봇 토큰과 챗 ID, API 키 설정
# ==========================================
GEMINI_API_KEY = "AQ.Ab8RN6JHYSC3NtrAipp-tVN1Ji2nK9z-TSAUDc5VLbyr57GprQ"
TELEGRAM_BOT_TOKEN = "8797523125:AAHYzdzNqa3tNVrkH59wRsrhtucoqCvfOKA"
TELEGRAM_CHAT_ID = "184097714"

# 구글 공식 SDK에 API 키 등록
genai.configure(api_key=GEMINI_API_KEY)

# ==========================================
# 2. 실전 최적화 마스터 프롬프트
# ==========================================
prompt = """
[System Role]
너는 생성형 AI가 아니라, 검증된 출처에서 팩트만 복사해 오는 '기계적 팩트 파서(Fact Parser)'다. 데이터를 가공, 계산, 환산, 유추하여 소설을 쓰는 행위를 엄격히 금지한다.

[3대 절대 규칙]
1. 검증된 출처 (Whitelist):
- 국내: 연합뉴스, 연합인포맥스, 이데일리, 한국경제, 매일경제 한정
- 미국: CNBC, Reuters 최우선 탐색
2. 수치 및 단위 원본 유지:
- 기사에 명시된 숫자와 단위를 100% 그대로 복사한다. AI 임의로 환전하거나 조(兆)를 억(億)으로 변환하지 마라.
- 수치 앞에 마이너스(-) 기호나 '순매도' 워딩이 붙어 있다면 절대 '순매수' 특징주로 추출하지 않는다.
3. 시간 및 날짜 팩트 체크:
- 검색 시점 기준 가장 최신 기사를 최우선 수집한다. 과거 수치와 현재 수치를 명확히 구분하라.

[항목별 기계적 출력 포맷]
1. 국내장 마감 수급 및 특징주
- 포맷: [코스피/코스닥 + 주체명 순매수] 종목명 (수치+원문단위)
2. 미국 증시 주요 일정
- 포맷: [현지시간 O월 O일 / KST O일 O시] 지표/실적명
3. 미국 증시 전망 및 프리마켓
- 포맷: [출처 매체 - 기사 송고일시] "직역 문장" (핵심 원단어)
4. 개인 신용거래융자 잔고
- 포맷: [O월 O일 기준] 신용거래융자 잔고 O조 O천억 원

[Kill Switch]
명확한 팩트가 없다면 지어내지 말고 오직 아래 문장만 출력한다.
"검증된 출처에서 기준에 부합하는 명확한 팩트가 확인되지 않아 작성을 생략합니다."
"""

# ==========================================
# 3. AI 실행 및 텔레그램 발송
# ==========================================
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    safe_text = text[:4000]
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": safe_text})

try:
    print("🔍 1단계: API 키에 허락된 AI 모델을 자동 검색합니다...")
    
    valid_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            valid_models.append(m.name)
            
    if not valid_models:
        raise Exception("해당 API 키로 텍스트 생성을 지원하는 모델이 없습니다.")
        
    # 고객님의 키에서 읽어온 '첫 번째 실제 모델 이름'을 강제 적용
    target_model = valid_models[0]
    print(f"🚀 2단계: 자동 선택된 모델({target_model})로 시황 분석을 시작합니다...\n")
    
    model = genai.GenerativeModel(target_model)
    response = model.generate_content(prompt)
    
    report = response.text
    
    print("========== [수집된 시황 브리핑 원본] ==========")
    print(report)
    print("==============================================\n")
    
    send_telegram_message(report)
    print("✅ 텔레그램 발송 완벽 성공! (휴대폰을 확인해주세요)")

except Exception as e:
    error_msg = f"🚨 시스템 오류 발생: {e}"
    print(error_msg)
    send_telegram_message(error_msg)
