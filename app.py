# app.py
from flask import Flask, render_template, jsonify, request
import json
import os
import google.generativeai as genai
from dotenv import load_dotenv

# 환경 변수 로드 (로컬 개발 시에만)
load_dotenv()

# Flask 애플리케이션 생성
app = Flask(__name__)

# Google AI API 설정
GCP_API_KEY = os.getenv("GCP_API_KEY")
if GCP_API_KEY:
    genai.configure(api_key=GCP_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
else:
    print("경고: GCP_API_KEY가 설정되지 않았습니다. AI 기능이 제한됩니다.")
    model = None

# 데이터베이스 역할을 할 JSON 파일 로드
CURRICULUM_DATA = {}
try:
    # 파일 경로를 현재 디렉토리 기준으로 설정
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, 'middle_school_data.json')
    
    with open(json_path, 'r', encoding='utf-8') as f:
        CURRICULUM_DATA = json.load(f)
    print(f"교육과정 데이터 로드 완료: {len(CURRICULUM_DATA)}개 항목")
except FileNotFoundError:
    print("경고: middle_school_data.json 파일을 찾을 수 없습니다.")
except Exception as e:
    print(f"데이터 로딩 오류: {e}")

# --- API 엔드포인트 정의 ---

@app.route('/api/curriculum-data')
def get_curriculum_data():
    """
    전체 교육과정 데이터를 JSON 형태로 반환합니다.
    """
    return jsonify(CURRICULUM_DATA)

@app.route('/api/ask', methods=['POST'])
def ask_ai():
    """
    AI에게 질문을 보내고 답변을 받습니다.
    """
    try:
        data = request.get_json()
        question = data.get('question', '')
        code = data.get('code', '')
        
        if not question:
            return jsonify({'error': '질문이 제공되지 않았습니다.'}), 400
        
        # AI 모델이 없으면 샘플 응답 반환
        if not model:
            return jsonify({
                'answer': '현재 AI 서비스를 이용할 수 없습니다. 환경 변수(GCP_API_KEY)를 확인해주세요.'
            })
        
        # 선택된 교육과정 코드가 있으면 해당 내용을 컨텍스트로 추가
        context = ""
        if code and code in CURRICULUM_DATA:
            curriculum_info = CURRICULUM_DATA[code]
            context = f"""
[참고할 교육과정 정보 - {code}]
- 학습 목표: {curriculum_info.get('학습 목표', '')}
- 개념 설명: {curriculum_info.get('개념 설명', '')[:500]}...
- 대표 예제: {curriculum_info.get('대표 예제', '')[:300]}...
"""
        
        # AI에게 보낼 프롬프트 구성
        prompt = f"""
당신은 중학교 수학 교육 전문가입니다. 2022 개정 교육과정을 바탕으로 학생들의 질문에 친절하고 정확하게 답변해주세요.

{context}

학생의 질문: {question}

답변 시 다음을 고려해주세요:
- 학생의 수준에 맞는 쉬운 설명
- 구체적인 예시 제공
- 단계별 해결 과정
- 마크다운 형식으로 구조화된 답변
- 수식은 LaTeX 형식($..$ 또는 $$..$$)으로 표현
"""
        
        # Gemini API 호출
        response = model.generate_content(prompt)
        
        return jsonify({
            'answer': response.text
        })
        
    except Exception as e:
        print(f"AI 질문 처리 오류: {e}")
        return jsonify({
            'error': f'AI 서비스 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/health')
def health_check():
    """
    서버 상태 확인용 엔드포인트
    """
    return jsonify({
        'status': 'healthy',
        'data_loaded': len(CURRICULUM_DATA) > 0,
        'ai_available': model is not None
    })

@app.route('/')
def index():
    """
    메인 웹페이지를 렌더링합니다.
    """
    return render_template('index.html')

# Vercel용 WSGI 애플리케이션 객체
application = app

# 서버 실행 (로컬 개발 시에만)
if __name__ == '__main__':
    app.run(debug=True, port=5001)
