import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import urllib3

# SSL 인증서 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 1. 미술관 목록 (요청하신 5곳 제외)
museums = [
    {"name": "경남도립미술관", "url": "https://www.gyeongnam.go.kr/gam/board/list.gyeong?boardId=BBS_0001504&menuCd=DOM_000003405000000000&contentsSid=5850&cpath=%2Fgam"},
    {"name": "광주시립미술관", "url": "https://artmuse.gwangju.go.kr/bb/bbBoard.php?boardID=NEWS&pageID=artmuse0501000000"},
    {"name": "대전시립미술관", "url": "https://www.daejeon.go.kr/dma/DmaBoardList.do?usrMenuCd=0601000000&menuSeq=6098"},
    {"name": "부산시립미술관", "url": "https://art.busan.go.kr/anucmt/list.nm"},
    {"name": "부산현대미술관", "url": "https://www.busan.go.kr/moca/news01"},
    {"name": "수원시립미술관", "url": "https://suma.suwon.go.kr/news/news_list.do"},
    {"name": "전북도립미술관", "url": "https://www.jma.go.kr/bbs/board.php?bo_id=notice"},
    {"name": "청주시립미술관", "url": "https://cmoa.cheongju.go.kr/www/selectBbsNttList.do?bbsNo=5&key=72"}
]

# 강력한 브라우저 위장 헤더
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
}

# 필터링 키워드
include_keywords = ["공고", "모집", "채용"]

# HTML 태그의 텍스트, 속성, 이미지 아이콘 검사
def is_valid_post(a_tag):
    texts = []
    
    if a_tag.get('title'):
        texts.append(a_tag.get('title'))
        
    texts.append(a_tag.get_text(separator=' ', strip=True))
    
    for img in a_tag.find_all('img'):
        if img.get('alt'):
            texts.append(img.get('alt'))
            
    raw_title = ' '.join(texts)
    title_clean = re.sub(r'\s+', ' ', raw_title).strip()
    
    if len(title_clean) < 4:
        return False, ""
        
    if any(keyword in title_clean for keyword in include_keywords):
        return True, title_clean
        
    return False, ""

# JS 링크를 실제 상세페이지 주소로 변환
def resolve_js_link(name, url, a_tag):
    href = a_tag.get('href', '').strip()
    onclick = a_tag.get('onclick', '').strip()
    
    target_script = href if href.startswith('javascript:') else (onclick if onclick else '')

    if target_script:
        numbers = re.findall(r"['\"]([^'\"]+)['\"]|\b(\d+)\b", target_script)
        extracted_params = [n[0] or n[1] for n in numbers if n[0] or n[1]]
        
        if extracted_params:
            post_id = extracted_params[0]
            if name == "부산시립미술관":
                return f"https://art.busan.go.kr/anucmt/view.nm?id={post_id}"
            elif name == "청주시립미술관":
                return f"https://cmoa.cheongju.go.kr/www/selectBbsNttView.do?bbsNo=5&nttNo={post_id}&key=72"
            
    return requests.compat.urljoin(url, href)

def crawl_sites():
    results = {}
    session = requests.Session()
    
    for museum in museums:
        name = museum['name']
        url = museum['url']
        results[name] = []
        
        try:
            session.headers.update(headers)
            if name == "청주시립미술관":
                session.headers.update({'Referer': url})
            else:
                session.headers.update({'Referer': ''})
                
            response = session.get(url, verify=False, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            count = 0 
            for a_tag in soup.find_all('a'):
                if count >= 30: 
                    break
                    
                is_valid, clean_title = is_valid_post(a_tag)
                
                if is_valid:
                    full_link = resolve_js_link(name, url, a_tag)
                    
                    if not any(item['link'] == full_link for item in results[name]):
                        results[name].append({"title": clean_title, "link": full_link})
                        count += 1
                        
        except requests.exceptions.ConnectionError:
            results[name].append({"title": "⚠️ 해당 기관 서버에서 접근을 차단했습니다.", "link": "#"})
        except Exception as e:
            print(f"Error crawling {name}: {e}")
            results[name].append({"title": f"⚠️ 데이터를 불러오는 중 오류 발생: {e}", "link": "#"})
            
    return results

def generate_html(data):
    # HTML 생성 템플릿 (디자인 변경 요청 반영: image_11.png 스타일)
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🏛️ 전국 공공미술관 채용 공고 모아보기</title>
        <style>
            /* 전체 스타일 - image_11.png의 깨끗하고 현대적인 분위기 재현 */
            body {{ font-family: 'Malgun Gothic', sans-serif; padding: 0; margin: 0; color: #333; background-color: #fff; line-height: 1.6; }}
            a {{ text-decoration: none; color: #333; }}
            a:hover {{ color: #a17056; }} /* 포인트 색상 */
            
            /* 헤더 스타일 */
            .main-header {{ text-align: center; padding: 30px 0; border-bottom: 1px solid #eee; }}
            .main-header h1 {{ font-size: 28px; margin: 0; font-weight: normal; }}
            .main-header .stats {{ font-size: 14px; color: #888; margin-top: 10px; }}
            .main-header .stats strong {{ color: #a17056; font-weight: normal; }} /* 포인트 색상 */
            
            /* 검색바 스타일 - 스타일만 구현 */
            .search-bar {{ text-align: center; margin-top: 20px; }}
            .search-bar input[type="text"] {{ padding: 10px 15px; border: 1px solid #ddd; width: 300px; font-size: 14px; }}
            .search-bar button {{ padding: 10px 20px; border: none; background-color: #333; color: white; cursor: pointer; font-size: 14px; margin-left: 10px; }}
            .search-bar button:hover {{ background-color: #555; }}
            
            /* 서브 메뉴 / 탭 스타일 - image_11.png의 텍스트 메뉴 스타일 */
            .sub-menu {{ text-align: center; margin-top: 30px; border-bottom: 1px solid #eee; }}
            .sub-menu-inner {{ display: inline-block; padding-bottom: 20px; }}
            .tablinks {{ background-color: inherit; border: none; outline: none; cursor: pointer; padding: 10px 15px; transition: 0.3s; font-size: 14px; color: #888; margin: 0 5px; border-bottom: 2px solid transparent; }}
            .tablinks:hover {{ color: #333; }}
            .tablinks.active {{ color: #333; border-bottom-color: #a17056; font-weight: bold; }} /* 활성화 시 포인트 색상 밑줄 */
            
            /* 콘텐츠 스타일 (테이블) */
            .content-container {{ max-width: 1000px; margin: 40px auto; padding: 0 20px; }}
            .tabcontent {{ display: none; }}
            
            /* 테이블 스타일 - image_11.png 완벽 재현 */
            .board-table {{ width: 100%; border-collapse: collapse; font-size: 14px; text-align: center; }}
            .board-table th {{ border-top: 2px solid #333; border-bottom: 1px solid #eee; padding: 15px; font-weight: bold; color: #333; background-color: #f9f9f9; }}
            .board-table th:first-child {{ border-left: none; }}
            .board-table th:last-child {{ border-right: none; }}
            .board-table td {{ border-bottom: 1px solid #eee; padding: 15px; color: #666; }}
            .board-table td:nth-child(3) {{ text-align: left; }} /* 제목은 왼쪽 정렬 */
            .board-table tr:hover td {{ background-color: #f9f9f9; }} /* 호버 시 배경색 */
            
            /* 드롭다운 스타일 - 스타일만 구현 */
            .select-category {{ padding: 5px 10px; border: 1px solid #ddd; font-size: 12px; }}
            
            /* 페이지네이션 스타일 - image_11.png 스타일만 구현 */
            .pagination {{ text-align: center; margin-top: 40px; margin-bottom: 60px; }}
            .pagination-inner {{ display: inline-block; }}
            .pagination a, .pagination span {{ display: inline-block; width: 30px; height: 30px; line-height: 30px; border: 1px solid #eee; color: #666; font-size: 13px; margin: 0 3px; border-radius: 2px; }}
            .pagination a:hover {{ background-color: #f9f9f9; color: #333; }}
            .pagination .active {{ background-color: #a17056; color: white; border-color: #a17056; }} /* 활성화 시 포인트 색상 */
            
            /* 푸터 스타일 - image_11.png 기반 심플 구현 */
            .main-footer {{ background-color: #222; color: #888; padding: 50px 0; font-size: 12px; }}
            .footer-inner {{ max-width: 1000px; margin: 0 auto; padding: 0 20px; }}
            .footer-logo {{ font-size: 20px; font-weight: bold; color: white; margin-bottom: 20px; }}
            .footer-links {{ margin-bottom: 20px; }}
            .footer-links a {{ color: #ccc; margin-right: 20px; }}
            .footer-links a:hover {{ color: white; }}
            .footer-copyright {{ }}
            .footer-social {{ text-align: right; margin-top: -20px; }}
            .footer-social a {{ display: inline-block; width: 30px; height: 30px; border: 1px solid #555; border-radius: 50%; color: #888; line-height: 30px; text-align: center; margin-left: 10px; }}
            .footer-social a:hover {{ background-color: #555; color: white; }}
        </style>
    </head>
    <body>
        <div class="main-header">
            <h1>NEWS</h1>
            <div class="stats">총 🏛️ <strong>{len(data.keys())}</strong>개의 미술관에서 🏛️ <strong>{sum(len(posts) for posts in data.values())}</strong>개의 채용 공고를 모았습니다.</div>
            <div class="stats">마지막 업데이트: 🏛️ {update_time}</div>
            
            <div class="search-bar">
                <input type="text" placeholder="검색어를 입력하세요.">
                <button>Search</button>
            </div>
        </div>

        <div class="sub-menu">
            <div class="sub-menu-inner">
    """
    
    # 탭 버튼 생성 (가나다순) - sub-menu 영역에 배치
    for i, name in enumerate(data.keys()):
        active_class = "active" if i == 0 else ""
        html += f'<button class="tablinks {active_class}" onclick="openTab(event, \'{name}\')">{name}</button>\n'
        
    html += """
            </div>
        </div>

        <div class="content-container">
    """
    
    # 탭 콘텐츠 생성 (테이블)
    for i, (name, posts) in enumerate(data.items()):
        display_style = "block" if i == 0 else "none"
        html += f'<div id="{name}" class="tabcontent" style="display:{display_style}">\n'
        html += f'  <h3 style="margin-top: 0; margin-bottom: 20px;">{name} 채용 공고</h3>\n'
        
        # 테이블 헤더 생성 - image_11.png와 동일 구조
        html += """
            <table class="board-table">
                <thead>
                    <tr>
                        <th width="80">NO</th>
                        <th width="120">
                            <select class="select-category">
                                <option>분류</option>
                                <option>채용/모집</option>
                            </select>
                        </th>
                        <th>제목</th>
                        <th width="120">작성일</th>
                        <th width="100">조회수</th>
                    </tr>
