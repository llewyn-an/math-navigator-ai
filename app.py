# app.py
from flask import Flask, render_template, jsonify, request
import json
import os
import google.generativeai as genai

# Flask 애플리케이션 생성
app = Flask(__name__)

# 데이터베이스 역할을 할 JSON 파일 로드
CURRICULUM_DATA = {}
try:
    with open('middle_school_data.json', 'r', encoding='utf-8') as f:
        CURRICULUM_DATA = json.load(f)
except FileNotFoundError:
    print("경고: middle_school_data.json 파일을 찾을 수 없습니다.")

# --- API 엔드포인트 정의 ---

@app.route('/api/curriculum-data')
def get_curriculum_data():
    """
    프론트엔드에 전체 교육과정 데이터를 JSON 형태로 제공하는 API
    """
    return jsonify(CURRICULUM_DATA)

@app.route('/api/ask', methods=['POST'])
def ask_ai():
    """
    프론트엔드로부터 질문을 받아 Gemini API를 호출하고 결과를 반환하는 API
    """
    # API 키를 환경 변수에서 안전하게 불러옵니다.
    api_key = os.environ.get('GCP_API_KEY')
    if not api_key:
        return jsonify({"error": "GCP_API_KEY가 서버 환경 변수에 설정되지 않았습니다."}), 500

    # Google AI SDK 설정
    try:
        genai.configure(api_key=api_key)
        # 사용할 Gemini 모델을 지정합니다.
        model = genai.GenerativeModel('gemini-2.0-flash') 
    except Exception as e:
        print(f"API 키 설정 오류: {e}")
        return jsonify({"error": "API 키 설정에 실패했습니다. 유효한 키인지 확인해주세요."}), 500

    # 사용자 요청 데이터 파싱
    data = request.json
    user_input = data.get('question', '')
    selected_code = data.get('code', '')

    context = "일반적인 수학 질문에 답해주세요."
    if selected_code and selected_code in CURRICULUM_DATA:
        context = f"현재 선택된 교육과정 성취기준 코드는 {selected_code}입니다. 다음은 해당 내용입니다:\n\n" + json.dumps(CURRICULUM_DATA[selected_code], ensure_ascii=False, indent=2)

    system_prompt = f"""
    당신은 'Math Navigator AI'라는 이름의 친절하고 유능한 한국 중학교 수학 보조교사입니다.
    당신의 모든 답변은 2022 개정 대한민국 수학 교육과정에 기반해야 합니다.
    학생, 교사, 학부모가 이해하기 쉽게 설명하고, 필요시 LaTeX 문법($...$ 또는 $$...$$)을 사용하여 수식을 표현해주세요.
    
    **답변 작성 규칙:**
    1. 제목과 소제목을 사용하여 내용을 구조화하세요 (# ## ### 사용)
    2. 수식은 반드시 LaTeX 형식으로 작성하고, 복잡한 수식은 별도 줄에 $$...$$로 표시하세요
    3. 단계별 풀이는 번호를 매겨 명확히 구분하세요
    4. 중요한 개념이나 답은 **굵은 글씨**로 강조하세요
    5. 팁이나 주의사항은 > 인용문 형식으로 작성하세요
    6. 문단 사이에 적절한 공백을 두어 가독성을 높이세요
    7. 예시나 연습문제는 목록 형태로 정리하세요
    
    다음은 현재 사용자가 보고 있는 교육과정 내용입니다. 이 내용을 최우선으로 참고하여 답변하세요.
    --- 교육과정 내용 ---
    {context}
    --------------------
    """
    
    full_prompt = system_prompt + "\n\n사용자 질문: " + user_input
    
    try:
        # SDK를 사용하여 콘텐츠 생성
        response = model.generate_content(full_prompt)
        return jsonify({"answer": response.text})
    except Exception as e:
        print(f"API 호출 오류: {e}")
        error_message = str(e)
        if "API key not valid" in error_message:
            error_message = "API 키가 유효하지 않습니다. 키를 다시 확인해주세요."
        # 아래 줄의 오타를 수정했습니다.
        return jsonify({"error": f"AI 모델 호출 중 오류 발생: {error_message}"}), 500


# --- 웹페이지 라우팅 ---

@app.route('/')
def index():
    """
    메인 웹페이지를 렌더링합니다.
    """
    return render_template('index.html')

# 서버 실행
if __name__ == '__main__':
    app.run(debug=True, port=5001)
