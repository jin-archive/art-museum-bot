import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

# 1. 미술관 목록 및 URL (서울시립미술관 URL 수정)
museums = [
    {"name": "경남도립미술관", "url": "https://www.gyeongnam.go.kr/gam/board/list.gyeong?boardId=BBS_0001504&menuCd=DOM_000003405000000000&contentsSid=5850&cpath=%2Fgam"},
    {"name": "광주시립미술관", "url": "https://artmuse.gwangju.go.kr/bb/bbBoard.php?boardID=NEWS&pageID=artmuse0501000000"},
    {"name": "국립현대미술관", "url": "https://www.mmca.go.kr/pr/employmentList.do"},
    {"name": "대구미술관", "url": "https://daeguartmuseum.or.kr/index.do?menu_id=00000791"},
    {"name": "대전시립미술관", "url": "https://www.daejeon.go.kr/dma/DmaBoardList.do?usrMenuCd=0601000000&menuSeq=6098"},
    {"name": "부산시립미술관", "url": "https://art.busan.go.kr/anucmt/list.nm"},
    {"name": "부산현대미술관", "url": "https://www.busan.go.kr/moca/news01"},
    {"name": "서울시립미술관", "url": "https://sema.seoul.go.kr/kr/bbs/611389/getList"}, # 일반 리스트 URL로 변경
    {"name": "수원시립미술관", "url": "https://suma.suwon.go.kr/news/news_list.do"},
    {"name": "울산시립미술관", "url": "https://www.ulsan.go.kr/s/uam/bbs/list.ulsan?bbsId=BBS_0000000000000188&mId=001007002001000000"},
    {"name": "전남도립미술관", "url": "https://artmuseum.jeonnam.go.kr/www/1011?pageIndex=1&bbsSeq=2&clSeq=2&condition=&keyword=&pageUnit=10&order=INSERT_DT_DESC&url=%2Fwww%2Fbbs%2Fview%2Fpost%2Flist"},
    {"name": "전북도립미술관", "url": "https://www.jma.go.kr/bbs/board.php?bo_id=notice"},
    {"name": "청주시립미술관", "url": "https://cmoa.cheongju.go.kr/www/selectBbsNttList.do?bbsNo=5&key=72"},
    {"name": "포항시립미술관", "url": "https://poma.pohang.go.kr/poma/bbs/board.php?bo_table=notice"}
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# 2. 키워드 설정 (조건 업데이트)
include_keywords = ["채용", "모집", "시험", "근로자", "노동자", "직원", "공무원", "공무직", "기간제"]
exclude_keywords = ["서류", "면접", "합격"]

def filter_by_keywords(title):
    title_clean = re.sub(r'\s+', ' ', title).strip() # 공백, 줄바꿈 제거하여 한 줄로 정규화
    
    # 5글자 이하의 무의미한 링크(예: 페이지 번호 등) 제외
    if len(title_clean) < 5:
        return False

    # 포함 키워드 OR 조건
    if not any(kw in title_clean for kw in include_keywords):
        return False
    
    # 제외 키워드 AND 조건
    if any(kw in title_clean for kw in exclude_keywords):
        return False
        
    return True

# JS 링크(about:blank 방지)를 실제 상세주소로 변환하는 함수
def resolve_js_link(name, url, a_tag):
    href = a_tag.get('href', '').strip()
    onclick = a_tag.get('onclick', '').strip()
    
    # href나 onclick에 javascript가 포함된 경우
    target_script = ""
    if href.startswith('javascript:'):
        target_script = href
    elif onclick and (href == '#' or 'void(0)' in href.lower() or href == ''):
        target_script = onclick

    # JS 링크가 발견된 경우
    if target_script:
        # 괄호 안의 숫자(ID) 추출
        numbers = re.findall(r"['\"]([^'\"]+)['\"]|\b(\d+)\b", target_script)
        extracted_params = [n[0] or n[1] for n in numbers if n[0] or n[1]]
        
        if extracted_params:
            post_id = extracted_params[0]
            # 각 미술관별 상세페이지 URL 패턴 조립
            if name == "대구미술관":
                return f"https://daeguartmuseum.or.kr/index.do?menu_id=00000791&board_seq={post_id}"
            elif name == "부산시립미술관":
                return f"https://art.busan.go.kr/anucmt/view.nm?id={post_id}"
            elif name == "국립현대미술관":
                return f"https://www.mmca.go.kr/pr/employmentDetail.do?empId={post_id}"
            elif name == "청주시립미술관":
                return f"https://cmoa.cheongju.go.kr/www/selectBbsNttView.do?bbsNo=5&nttNo={post_id}&key=72"
            
    # 일반적인 링크인 경우 URL 결합
    return requests.compat.urljoin(url, href)

def crawl_sites():
    results = {}
    session = requests.Session()
    
    for museum in museums:
        name = museum['name']
        url = museum['url']
        results[name] = []
        
        try:
            # 청주시립미술관 Referer 우회 유지
            if name == "청주시립미술관":
                session.headers.update({'Referer': url})
            else:
                session.headers.update({'Referer': ''})
                
            response = session.get(url, headers=headers, verify=False, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for a_tag in soup.find_all('a'):
                # 태그 안의 텍스트를 공백으로 구분하여 추출 (숨겨진 태그 대비)
                title = a_tag.get_text(separator=' ', strip=True)
                title_clean = re.sub(r'\s+', ' ', title)
                
                if filter_by_keywords(title_clean):
                    # 빈 링크 버그를 방지하는 강력한 URL 생성
                    full_link = resolve_js_link(name, url, a_tag)
                    
                    if not any(item['link'] == full_link for item in results[name]):
                        results[name].append({"title": title_clean, "link": full_link})
        except Exception as e:
            print(f"Error crawling {name}: {e}")
            
    return results

def generate_html(data):
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🏛️ 전국 공공미술관 채용/모집 공고 모아보기</title>
        <style>
            body {{ font-family: 'Malgun Gothic', sans-serif; padding: 20px; max-width: 800px; margin: auto; }}
            .header {{ text-align: center; margin-bottom: 20px; }}
            .tab {{ overflow: hidden; border: 1px solid #ccc; background-color: #f1f1f1; display: flex; flex-wrap: wrap; }}
            .tab button {{ background-color: inherit; border: none; outline: none; cursor: pointer; padding: 10px 15px; transition: 0.3s; font-size: 14px; }}
            .tab button:hover {{ background-color: #ddd; }}
            .tab button.active {{ background-color: #007bff; color: white; font-weight: bold; }}
            .tabcontent {{ display: none; padding: 15px; border: 1px solid #ccc; border-top: none; animation: fadeEffect 0.5s; }}
            @keyframes fadeEffect {{ from {{opacity: 0;}} to {{opacity: 1;}} }}
            ul {{ list-style-type: none; padding: 0; }}
            li {{ margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px dashed #eee; line-height: 1.5; }}
            a {{ text-decoration: none; color: #333; }}
            a:hover {{ color: #007bff; font-weight: bold; text-decoration: underline; }}
            .empty {{ color: #999; font-style: italic; text-align: center; padding: 20px; }}
            .filter-info {{ background: #f8f9fa; padding: 10px; border-radius: 5px; font-size: 13px; color: #555; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>🏛️ 전국 공공미술관 채용/모집 공고</h2>
            <div class="filter-info">
                <strong>포함:</strong> {', '.join(include_keywords)}<br>
                <strong>제외:</strong> {', '.join(exclude_keywords)}
            </div>
            <p><small>업데이트 시간: {update_time}</small></p>
        </div>

        <div class="tab">
    """
    
    for i, name in enumerate(data.keys()):
        active_class = "active" if i == 0 else ""
        html += f'<button class="tablinks {active_class}" onclick="openTab(event, \'{name}\')">{name}</button>\n'
        
    html += "</div>\n\n"
    
    for i, (name, posts) in enumerate(data.items()):
        display_style = "block" if i == 0 else "none"
        html += f'<div id="{name}" class="tabcontent" style="display:{display_style}">\n'
        html += f'  <h3>{name}</h3>\n  <ul>\n'
        
        if posts:
            for post in posts:
                html += f'    <li><a href="{post["link"]}" target="_blank">📄 {post["title"]}</a></li>\n'
        else:
            html += f'    <li class="empty">현재 조건에 맞는 공고가 없습니다.</li>\n'
            
        html
