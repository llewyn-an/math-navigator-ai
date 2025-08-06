# parser.py
import re
import json

def parse_curriculum_file(input_filename, output_filename):
    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"오류: '{input_filename}' 파일을 찾을 수 없습니다.")
        return

    # 성취기준 코드와 그 다음 내용을 찾는 패턴
    pattern = r'#### [^(]*\((\[9수\d{2}-\d{2,}\])\)'
    
    # finditer를 사용하여 각 성취기준 섹션을 찾습니다
    matches = list(re.finditer(pattern, content))
    
    structured_data = {}
    
    print(f"총 {len(matches)}개의 성취기준을 찾았습니다.")
    
    for i, match in enumerate(matches):
        code = match.group(1)  # [9수01-01] 형태의 코드
        start_pos = match.end()
        
        # 다음 성취기준까지의 내용을 가져옵니다
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
            text_block = content[start_pos:end_pos]
        else:
            # 마지막 항목인 경우 끝까지 가져옵니다
            text_block = content[start_pos:]
            # ---를 만나면 거기서 끝
            dash_pos = text_block.find('\n---')
            if dash_pos != -1:
                text_block = text_block[:dash_pos]
        
        print(f"파싱 중: {code}")
        
        item_data = {}
        
        # 각 섹션을 찾는 개선된 정규식 패턴들
        sections = {
            "학습 목표": r'\*\*학습 목표\*\*\s*\n(.*?)(?=\n\*\*[^*]|$)',
            "개념 설명": r'\*\*개념 설명\*\*\s*\n(.*?)(?=\n\*\*[^*]|$)',
            "대표 예제": r'\*\*대표 예제\*\*\s*\n(.*?)(?=\n\*\*[^*]|$)',
            "연습 문제": r'\*\*연습 문제\*\*\s*\n(.*?)(?=\n\*\*[^*]|$)',
            "정답 및 해설": r'\*\*정답 및 해설\*\*\s*\n(.*?)(?=\n\*\*[^*]|$)',
            "마스터리 드릴": r'\*\*마스터리 드릴\*\*\s*\n(.*?)(?=\n\*\*[^*]|$)',
            "진단 체크": r'\*\*진단 체크\*\*\s*\n(.*?)(?=\n\*\*[^*]|$)',
            "확장 활동": r'\*\*확장 활동\*\*\s*\n(.*?)(?=\n\*\*[^*]|$)',
            "튜터 팁": r'\*\*튜터 팁\*\*\s*\n(.*?)(?=\n---|$)',
        }
        
        for section_name, section_pattern in sections.items():
            match_section = re.search(section_pattern, text_block, re.DOTALL)
            if match_section:
                content_text = match_section.group(1).strip()
                if content_text and content_text != "*":  # 빈 내용이나 "*"만 있는 경우 제외
                    item_data[section_name] = content_text
                    print(f"  - {section_name}: 찾음 ({len(content_text)} 문자)")
                else:
                    print(f"  - {section_name}: 빈 내용 또는 '*'만 있음")
            else:
                print(f"  - {section_name}: 찾지 못함")
        
        if item_data:  # 데이터가 있는 경우만 추가
            structured_data[code] = item_data
        else:
            print(f"  ⚠️ {code}: 파싱된 데이터가 없습니다!")

    # 디버깅을 위해 첫 번째 항목의 상세 정보 출력
    if structured_data:
        first_key = list(structured_data.keys())[0]
        print(f"\n=== {first_key} 디버깅 정보 ===")
        for section, content in structured_data[first_key].items():
            print(f"{section}: {content[:100]}..." if len(content) > 100 else f"{section}: {content}")

    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(structured_data, f, ensure_ascii=False, indent=2)

    print(f"\n성공: '{output_filename}' 파일이 생성되었습니다. ({len(structured_data)}개 항목)")

if __name__ == "__main__":
    parse_curriculum_file('curriculum_middle.md', 'middle_school_data.json')