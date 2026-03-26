import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

# 1. 미술관 목록 및 URL
museums = [
    {"name": "경남도립미술관", "url": "https://www.gyeongnam.go.kr/gam/board/list.gyeong?boardId=BBS_0001504&menuCd=DOM_000003405000000000&contentsSid=5850&cpath=%2Fgam"},
    {"name": "광주시립미술관", "url": "https://artmuse.gwangju.go.kr/bb/bbBoard.php?boardID=NEWS&pageID=artmuse0501000000"},
    {"name": "국립현대미술관", "url": "https://www.mmca.go.kr/pr/employmentList.do"},
    {"name": "대구미술관", "url": "https://daeguartmuseum.or.kr/index.do?menu_id=00000791"},
    {"name": "대전시립미술관", "url": "https://www.daejeon.go.kr/dma/DmaBoardList.do?usrMenuCd=0601000000&menuSeq=6098"},
    {"name": "부산시립미술관", "url": "https://art.busan.go.kr/anucmt/list.nm"},
    {"name": "부산현대미술관", "url": "https://www.busan.go.kr/moca/news01"},
    {"name": "서울시립미술관", "url": "https://sema.seoul.go.kr/kr/bbs/611389/getList"},
    {"name": "수원시립미술관", "url": "https://suma.suwon.go.kr/news/news_list.do"},
    {"name": "울산시립미술관", "url": "https://www.ulsan.go.kr/s/uam/bbs/list.ulsan?bbsId=BBS_0000000000000188&mId=001007002001000000"},
    {"name": "전남도립미술관", "url": "https://artmuseum.jeonnam.go.kr/www/1011?pageIndex=1&bbsSeq=2&clSeq=2&condition=&keyword=&pageUnit=10&order=INSERT_DT_DESC&url=%2Fwww%2Fbbs%2Fview%2Fpost%2Flist"},
    {"name": "전북도립미술관", "url": "https://www.jma.go.kr/bbs/board.php?bo_id=notice"},
    {"name": "청주시립미술관", "url": "https://cmoa.cheongju.go.kr/www/selectBbsNttList.do?bbsNo=5&key=72"},
    {"name": "포항시립미술관", "url": "https://poma.pohang.go.kr/poma/bbs/board.php?bo_table=notice"}
]

# 해외 IP 차단(WAF)을 최대한 우회하기 위한 브라우저 위장 헤더
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive'
}

# 불필요한 UI 링크(게시글이 아닌 링크)를 걸러내는 함수
def is_valid_post(title):
    title_clean = re.sub(r'\s+', ' ', title).strip()
    
    # 너무 짧은 텍스트(예: "1", "다음", "NEW") 제외
    if len(title_clean) < 6:
        return False, ""
        
    # 메뉴나 하단 푸터에 있는 일반적인 단어들 제외
    ignore_words = ['개인정보', '이용약관', '저작권', '홈페이지', '본문으로', '오시는길', '사이트맵']
    if any(word in title_clean for word in ignore_words):
        return False, ""
        
    return True, title_clean

# JS 링크를 실제 상세주소로 변환하는 함수
def resolve_js_link(name, url, a_tag):
    href = a_tag.get('href', '').strip()
    onclick = a_tag.get('onclick', '').strip()
    
    target_script = href if href.startswith('javascript:') else (onclick if onclick else '')

    if target_script:
        numbers = re.findall(r"['\"]([^'\"]+)['\"]|\b(\d+)\b", target_script)
        extracted_params = [n[0] or n[1] for n in numbers if n[0] or n[1]]
        
        if extracted_params:
            post_id = extracted_params[0]
            if name == "대구미술관":
                return f"https://daeguartmuseum.or.kr/index.do?menu_id=00000791&board_seq={post_id}"
            elif name == "부산시립미술관":
                return f"https://art.busan.go.kr/anucmt/view.nm?id={post_id}"
            elif name == "국립현대미술관":
                return f"https://www.mmca.go.kr/pr/employmentDetail.do?empId={post_id}"
            elif name == "청주시립미술관":
                return f"https://cmoa.cheongju.go.kr/www/selectBbsNttView.do?bbsNo=5&nttNo={post_id}&key=72"
            elif name == "서울시립미술관":
                return f"https://sema.seoul.go.kr/kr/bbs/611389/detail.nm?bbsId=611389&nttId={post_id}"
            
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
                
            response = session.get(url, verify=False, timeout=15)
            response.encoding = 'utf-8' # 한글 깨짐 방지
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 한 미술관당 최대 15개까지만 가져오기 (게시판 전체 도배 방지)
            count = 0 
            for a_tag in soup.find_all('a'):
                if count >= 15:
                    break
                    
                raw_title = a_tag.get_text(separator=' ', strip=True)
                is_valid, clean_title = is_valid_post(raw_title)
                
                if is_valid:
                    full_link = resolve_js_link(name, url, a_tag)
                    
                    # 중복 링크 방지
                    if not any(item['link'] == full_link for item in results[name]):
                        results[name].append({"title": clean_title, "link": full_link})
                        count += 1
                        
        except requests.exceptions.ConnectionError:
            results[name].append({"title": "⚠️ 해당 기관 서버에서 해외 IP(깃허브 액션) 접속을 차단했습니다.", "link": "#"})
        except Exception as e:
            print(f"Error crawling {name}: {e}")
            results[name].append({"title": f"⚠️ 데이터를 불러오는 중 오류 발생: {e}", "link": "#"})
            
    return results

def generate_html(data):
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🏛️ 전국 공공미술관 게시판 모아보기</title>
        <style>
            body {{ font-family: 'Malgun Gothic', sans-serif; padding: 20px; max-width: 900px; margin: auto; }}
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
        </style>
    </head>
    <body>
        <div class="header">
            <h2>🏛️ 전국 공공미술관 게시판 모아보기 (전체글)</h2>
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
                # 에러 메시지인 경우 링크 스타일 다르게 처리
                if post["link"] == "#":
                    html += f'    <li style="color:red;">{post["title"]}</li>\n'
                else:
                    html += f'    <li><a href="{post["link"]}" target="_blank">📄 {post["title"]}</a></li>\n'
        else:
            html += f'    <li class="empty">게시글을 불러오지 못했습니다.</li>\n'
            
        html += "  </ul>\n</div>\n"
        
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
