import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

# 1. 미술관 목록 (가나다 순 정렬)
museums = [
    {"name": "경남도립미술관", "url": "https://www.gyeongnam.go.kr/gam/board/list.gyeong?boardId=BBS_0001504&menuCd=DOM_000003405000000000&contentsSid=5850&cpath=%2Fgam"},
    {"name": "광주시립미술관", "url": "https://artmuse.gwangju.go.kr/bb/bbBoard.php?boardID=NEWS&pageID=artmuse0501000000"},
    {"name": "국립현대미술관", "url": "https://www.mmca.go.kr/pr/employmentList.do"},
    {"name": "대구미술관", "url": "https://daeguartmuseum.or.kr/index.do?menu_id=00000791"},
    {"name": "대전시립미술관", "url": "https://www.daejeon.go.kr/dma/DmaBoardList.do?usrMenuCd=0601000000&menuSeq=6098"},
    {"name": "부산시립미술관", "url": "https://art.busan.go.kr/anucmt/list.nm"},
    {"name": "부산현대미술관", "url": "https://www.busan.go.kr/moca/news01"},
    {"name": "서울시립미술관", "url": "https://sema.seoul.go.kr/kr/bbs/611389/getBbsList"}, # API URL
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

# 2. 키워드 설정
include_keywords = ["채용", "모집", "시험", "근로자", "노동자", "직원", "공무원", "공무직", "기간제"]
exclude_keywords = ["서류", "면접", "합격"]

def filter_by_keywords(title):
    # 대소문자 구분 없이 필터링
    title_lower = title.lower()
    
    # 포함 키워드 OR 조건
    if not any(kw in title_lower for kw in include_keywords):
        return False
    
    # 제외 키워드 AND 조건
    if any(kw in title_lower for kw in exclude_keywords):
        return False
        
    return True

def crawl_sites():
    results = {}
    for museum in museums:
        name = museum['name']
        url = museum['url']
        results[name] = []
        
        try:
            # 특수 케이스 처리: 서울시립미술관 (API/JSON)
            if name == "서울시립미술관":
                api_response = requests.get(url, headers=headers, verify=False, timeout=10)
                data = api_response.json()
                
                # SeMA JSON 구조에서 데이터 추출 (가정: 'nttList' 또는 'list' 아래에 항목이 있음)
                post_items = data.get('nttList') or data.get('list') or []
                
                for item in post_items:
                    # 'nttSj'는 제목, 'nttId'는 고유 ID
                    title = item.get('nttSj')
                    ntt_id = item.get('nttId')
                    
                    if title and filter_by_keywords(title) and ntt_id:
                        # 상세 페이지 URL 패턴 생성
                        full_link = f"https://sema.seoul.go.kr/kr/bbs/611389/detail.nm?bbsId=611389&nttId={ntt_id}"
                        
                        if not any(i['link'] == full_link for i in results[name]):
                            results[name].append({"title": title, "link": full_link})
                continue # SeMA는 JSON 처리로 종료
                
            # 특수 케이스 처리: 청주시립미술관 (Referer 헤더 필요)
            session = requests.Session()
            if name == "청주시립미술관":
                # 세션을 사용하여 Referer 추가
                session.headers.update({
                    'User-Agent': headers['User-Agent'],
                    'Referer': url # 목록 페이지 자체를 Referer로 설정
                })
                response = session.get(url, verify=False, timeout=10)
            else:
                response = session.get(url, headers=headers, verify=False, timeout=10)
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 모든 a 태그를 검색하여 게시글 제목 추출 (실제 운영시 사이트별 정확한 selector 사용 권장)
            for a_tag in soup.find_all('a'):
                title = a_tag.get_text(strip=True)
                href = a_tag.get('href', '')
                
                if filter_by_keywords(title):
                    # requests.compat.urljoin을 사용하여 SuMA 등의 링크 문제 완벽 해결
                    full_link = requests.compat.urljoin(url, href)
                    
                    if not any(item['link'] == full_link for item in results[name]):
                        results[name].append({"title": title, "link": full_link})
        except Exception as e:
            print(f"Error crawling {name}: {e}")
            
    return results

def generate_html(data):
    # HTML 생성 템플릿 (Tab UI 및 가나다순 정렬 적용)
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
            /* 탭 스타일 */
            .tab {{ overflow: hidden; border: 1px solid #ccc; background-color: #f1f1f1; display: flex; flex-wrap: wrap; }}
            .tab button {{ background-color: inherit; border: none; outline: none; cursor: pointer; padding: 10px 15px; transition: 0.3s; font-size: 14px; }}
            .tab button:hover {{ background-color: #ddd; }}
            .tab button.active {{ background-color: #007bff; color: white; }}
            /* 탭 콘텐츠 스타일 */
            .tabcontent {{ display: none; padding: 15px; border: 1px solid #ccc; border-top: none; animation: fadeEffect 1s; }}
            @keyframes fadeEffect {{ from {{opacity: 0;}} to {{opacity: 1;}} }}
            ul {{ list-style-type: none; padding: 0; }}
            li {{ margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px dashed #eee; }}
            a {{ text-decoration: none; color: #333; }}
            a:hover {{ color: #007bff; font-weight: bold; }}
            .empty {{ color: #999; font-style: italic; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>🏛️ 전국 공공미술관 채용/모집 공고 모아보기</h2>
            <p><small>포함 키워드: {', '.join(include_keywords)} | 제외 키워드: {', '.join(exclude_keywords)}</small></p>
            <p><small>마지막 업데이트: {update_time}</small></p>
        </div>

        <div class="tab">
    """
    
    # 탭 버튼 생성 (가나다순)
    for i, name in enumerate(data.keys()):
        active_class = "active" if i == 0 else ""
        html += f'<button class="tablinks {active_class}" onclick="openTab(event, \'{name}\')">{name}</button>\n'
        
    html += "</div>\n\n"
    
    # 탭 콘텐츠 생성
    for i, (name, posts) in enumerate(data.items()):
        display_style = "block" if i == 0 else "none"
        html += f'<div id="{name}" class="tabcontent" style="display:{display_style}">\n'
        html += f'  <h3>{name}</h3>\n  <ul>\n'
        
        if posts:
            for post in posts:
                html += f'    <li><a href="{post["link"]}" target="_blank">📄 {post["title"]}</a></li>\n'
        else:
            html += f'    <li class="empty">현재 필터링 조건에 맞는 공고가 없습니다.</li>\n'
            
        html += "  </ul>\n</div>\n"
        
    # JavaScript 추가 (탭 동작 로직)
    html += """
        <script>
        function openTab(evt, tabName) {
            var i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tabcontent");
            for (i = 0; i < tabcontent.length; i++) {
                tabcontent[i].style.display = "none";
            }
            tablinks = document.getElementsByClassName("tablinks");
            for (i = 0; i < tablinks.length; i++) {
                tablinks[i].className = tablinks[i].className.replace(" active", "");
            }
            document.getElementById(tabName).style.display = "block";
            evt.currentTarget.className += " active";
        }
        </script>
    </body>
    </html>
    """
    
    return html

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    print("크롤링을 시작합니다...")
    crawled_data = crawl_sites()
    
    print("HTML 문서를 생성합니다...")
    html_output = generate_html(crawled_data)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_output)
        
    print("성공적으로 index.html을 생성했습니다.")
