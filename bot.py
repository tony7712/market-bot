import requests

# ==========================================
# 1. 봇 토큰과 챗 ID, API 키 설정
# ==========================================
GEMINI_API_KEY = "AQ.Ab8RN6JHYSC3NtrAipp-tVN1Ji2nK9z-TSAUDc5VLbyr57GprQ"
TELEGRAM_BOT_TOKEN = "8797523125:AAHYzdzNqa3tNVrkH59wRsrhtucoqCvfOKA"
TELEGRAM_CHAT_ID = "184097714"

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
# 3. AI 실행 및 텔레그램 발송 (자동 모델 추적 기능)
# ==========================================
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text[:4000]})

try:
    print("🔍 1단계: API 키에 허락된 AI 모델 목록을 구글에 직접 조회합니다...")
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    list_response = requests.get(list_url)
    
    if list_response.status_code != 200:
        raise Exception(f"모델 목록 조회 실패 (API 키 권한 문제일 수 있습니다): {list_response.text}")
        
    models_data = list_response.json().get('models', [])
    
    # generateContent(텍스트 생성) 기능을 지원하는 모델만 필터링
    valid_models = [m['name'] for m in models_data if 'generateContent' in m.get('supportedGenerationMethods', [])]
    
    if not valid_models:
        raise Exception("해당 API 키로 사용할 수 있는 텍스트 생성 모델이 하나도 존재하지 않습니다.")
        
    print(f"✅ 사용 가능한 모델 목록: {valid_models}")
    
    # 1.5-flash 모델을 우선적으로 찾고, 없으면 구글이 허락한 첫 번째 모델을 무조건 사용
    selected_model = valid_models[0]
    for model_name in valid_models:
        if "1.5-flash" in model_name:
            selected_model = model_name
            break
            
    print(f"🚀 최종 선택된 모델: {selected_model}")
    print("\n🌐 2단계: 선택된 모델로 시황 분석을 시작합니다...")
    
    # 선택된 모델 이름(예: models/gemini-1.5-flash)을 URL에 정확히 삽입
    model_path = selected_model if selected_model.startswith("models/") else f"models/{selected_model}"
    
    generate_url = f"https://generativelanguage.googleapis.com/v1beta/{model_path}:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    response = requests.post(generate_url, headers=headers, json=data)
    if response.status_code != 200:
        raise Exception(f"구글 API 에러: {response.text}")
        
    result_text = response.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '⚠️ 결과 없음')
    
    print("========== [수집된 시황 브리핑 원본] ==========")
    print(result_text)
    print("==============================================\n")
    
    send_telegram_message(result_text)
    print("✅ 텔레그램 발송 완벽 성공! (휴대폰을 확인해주세요)")

except Exception as e:
    error_msg = f"🚨 시스템 오류 발생: {e}"
    print(error_msg)
    send_telegram_message(error_msg)
