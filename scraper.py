import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

# 1. 가나다순으로 정렬된 미술관 목록 및 URL 데이터
museums = [
    {"name": "경남도립미술관", "url": "https://www.gyeongnam.go.kr/gam/board/list.gyeong?boardId=BBS_0001504&menuCd=DOM_000003405000000000&contentsSid=5850&cpath=%2Fgam"},
    {"name": "광주시립미술관", "url": "https://artmuse.gwangju.go.kr/bb/bbBoard.php?boardID=NEWS&pageID=artmuse0501000000"},
    {"name": "국립현대미술관", "url": "https://www.mmca.go.kr/pr/employmentList.do"},
    {"name": "대구미술관", "url": "https://daeguartmuseum.or.kr/index.do?menu_id=00000791"},
    {"name": "대전시립미술관", "url": "https://www.daejeon.go.kr/dma/DmaBoardList.do?usrMenuCd=0601000000&menuSeq=6098"},
    {"name": "부산시립미술관", "url": "https://art.busan.go.kr/anucmt/list.nm"},
    {"name": "부산현대미술관", "url": "https://www.busan.go.kr/moca/news01"},
    {"name": "서울시립미술관", "url": "https://sema.seoul.go.kr/kr/bbs/611389/getBbsList"},
    {"name": "수원시립미술관", "url": "https://suma.suwon.go.kr/news/news_list.do"},
    {"name": "울산시립미술관", "url": "https://www.ulsan.go.kr/s/uam/bbs/list.ulsan?bbsId=BBS_0000000000000188&mId=001007002001000000"},
    {"name": "전남도립미술관", "url": "https://artmuseum.jeonnam.go.kr/www/1011?pageIndex=1&bbsSeq=2&clSeq=2&condition=&keyword=&pageUnit=10&order=INSERT_DT_DESC&url=%2Fwww%2Fbbs%2Fview%2Fpost%2Flist"},
    {"name": "전북도립미술관", "url": "https://www.jma.go.kr/bbs/board.php?bo_id=notice"},
    {"name": "청주시립미술관", "url": "https://cmoa.cheongju.go.kr/www/selectBbsNttList.do?bbsNo=5&key=72"},
    {"name": "포항시립미술관", "url": "https://poma.pohang.go.kr/poma/bbs/board.php?bo_table=notice"}
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def crawl_sites():
    results = {}
    for museum in museums:
        name = museum['name']
        url = museum['url']
        results[name] = []
        
        try:
            # SSL 인증서 오류 무시 및 타임아웃 설정
            response = requests.get(url, headers=headers, verify=False, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 모든 a 태그를 검색하여 게시글 제목 추출 (실제 운영시 사이트별 정확한 selector 사용 권장)
            for a_tag in soup.find_all('a'):
                title = a_tag.get_text(strip=True)
                href = a_tag.get('href', '')
                
                # 조건 필터링: "채용"이 포함되어 있고, "합격"이 포함되지 않은 경우
                if "채용" in title and "합격" not in title:
                    # 상대경로인 경우 절대경로로 변환
                    full_link = href if href.startswith('http') else url.split('/')[0] + '//' + url.split('/')[2] + href
                    
                    # 중복 방지
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
        <title>전국 공공미술관 채용 공고 모아보기</title>
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
            <h2>🏛️ 전국 공공미술관 채용 공고 모아보기</h2>
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
            html += f'    <li class="empty">현재 진행 중인 채용 공고가 없습니다.</li>\n'
            
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
