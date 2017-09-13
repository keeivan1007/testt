import glob
import os

for v in glob.glob('./conf/*'):
    
    if v.find('`')<0 or os.isfile(v): # R修改
        continue
    
    info = {}
    info['path'] = v + '\\'
    info['board_name'] = v.split('`')[0].split('\\')[-1]
    begin(info)

# 起始區
def begin(info):

    import requests
    from bs4 import BeautifulSoup
    
    # 存取規則
    board_name = info['board_name'] # 讀取要爬取的版位名稱
    path = info['path']  # 讀取要存取的資料夾路徑
    load_json_rules = load_rules( path + 'rules.json') #存取規則
    load_json_rules['path'] = path
    

    #這裡抓總頁數
    HOST = "https://www.ptt.cc"
    res = requests.get(HOST + "/bbs/{}/index.html".format(board_name), headers={"cookie": "over18=1;"})
    soup = BeautifulSoup(res.text, 'lxml')
    buttons = soup.select('a.btn.wide')
    total_page = int(buttons[1]['href'].split('index')[1].split('.html')[0]) + 1

    #決定要爬幾個頁數
    page_to_crawl = load_json_rules['recent_page'] #讀取規則...確認要抓取的頁數
    for page in range(total_page, total_page - page_to_crawl, -1):
        url = 'https://www.ptt.cc/bbs/{}/index{}.html'.format(board_name,page)
        mainthread(url,load_json_rules)
        
        

        
        
#爬蟲區　每頁進行 
#主塊執行區
def mainthread(url,load_json_rules):

    import time
    from bs4 import BeautifulSoup

    articles= {} #　每一頁所有的文章都集結近來，先建立一個dict
    
    page = get_web_page(url) # 讓網址過滿十八歲的cookie
    
    if page: #判有無東西，此頁有無正常回傳
        articles = get_articles(page) # 蒐集資本資訊
    
    count = 0 #R暫時
    for article in articles: #　每一篇都跑，更新成進階資訊　→　驗證有無推過規則　→　儲存
        
        save_record = ''
        
        try:
            if '[公告]' in article['title'] : continue # 因為設計上應該在 ↓ compare_rules 跳出迴圈 ， 但因為 catch_info 進階內文就會跳出 error 故直接在這寫死剔除公告文，這不是個好的設計，是個可以改良的地方

            article = catch_info(article) #　蒐集進階內部資訊

            if compare_rules(article,load_json_rules) == True:
                save_text(article,load_json_rules['path']) # 輸入要儲存的物件跟路徑
                save_record = '【已儲存】'
            else:
                pass

            time.sleep(3) #設定睡覺時間 以免被擋掉
            count = count + 1 #R暫時
            print '此頁目前執行第{0}...【{1}】【已結束】 {2}\n'.format(count,article['title'],save_record) #R暫時
        except Exception as ex:
            print '在文章過濾階段某文發生程式以外錯誤\n在此跳過，錯誤訊息如下：\n{}'.format(ex)
            



"""
purpos:塞入cookie確認是否滿18;判別requests是否成功

輸入:將要解析資訊的網址
輸出:回傳request的值，檔案已是text檔!

"""

def get_web_page(url):  
    from bs4 import BeautifulSoup
    import requests
    resp = requests.get(url=url,cookies={'over18':'1'}) #塞入cookie over18:1
    if resp.status_code != 200:  #用200判別連線是否正常
        print 'Invalid url:',resp.url
        return None
    else:
        return resp.text #記住回傳是text!



#把每頁的文章資訊全部爬下來

def get_articles(dom):
    
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(dom, 'html.parser')

    articles = []  # 儲存取得的文章資料
    divs = soup.find_all('div', 'r-ent') #'r-ent'就是每篇文章的附屬資訊
    for d in divs:
        #if d.find('div', 'date').string.strip() == date:  # 發文日期正確才繼續 ,這裡原寫法沒strip沒去掉空白，已更正
        # 取得推文數
        push_count = 0
        if d.find('div', 'nrec').string: #nrec→是按讚數
            try:  #轉換成功 
                push_count = int(d.find('div', 'nrec').string)  # 轉換字串為數字
            except ValueError:  # 若轉換失敗，不做任何事，push_count 保持為 0
                pass
            # 取得文章連結及標題
        if d.find('a'):  # 網址跟標題都在a裡面 如果a沒有代表已被版主刪除 用來判斷內文存在不存在
            href = d.find('a')['href'] #把a裡面 - href取出來
            title = d.find('a').string #把a整串全部抓下來
            articles.append({
                'title': title,
                'href': href,
                'push_count': push_count
            })
    return articles




"""
purpose:讓每篇文章的爬文結果，對照規則

input:

1.article:文章的資訊包，包括作者、版位、時間...等規格，dict 格式,僅有一層關係

2.compare_rules:讀取好的規則,dict

output:

True or False

告知有無符合規則，只要符合List其中一個元素一次[]，則回傳

"""

def compare_rules(article,compare_rules):
    
    try:
        
        bool_has = True ; bool_not = True ; bool_author = True ; bool_push = True ; bool_cmt = True

        if compare_rules['has_title'] or compare_rules['has_content'] : bool_has = False # 如果標題_包含、內文_包含部分有輸入值，bool_has設False，來進行比對
        # bool_not的部分不用先變成 False ，因為有一個 not_內容_包含 被觸發，即時 bool_not = False
        if compare_rules['author'] : bool_author = False
        if compare_rules['push_count']  : bool_push = False
        if compare_rules['comment_content'] : bool_cmt = False


        if list_look_for(compare_rules['comment_content'],article['comment']):bool_cmt = True #　評論

        if list_look_for(compare_rules['has_title'],article['title']):bool_has = True # 標題＿包含
        if list_look_for(compare_rules['has_content'],article['content']):bool_has = True  # 內容＿包含

        if list_look_for(compare_rules['not_title'],article['title']):bool_not = False  # 標題＿不含
        if list_look_for(compare_rules['not_content'],article['content']):bool_not = False  # 內容＿不含

        if article['push_count'] >= compare_rules['push_count'] : bool_push = True  # 按讚數_不超過指定數量 False
        if article['author'] in compare_rules['author'] : bool_author = True # 如果作者正確，則對

        bool_str = '測試結果：\n' #R暫時 測試文字
        if bool_has: bool_str = bool_str + '擁有(過)'
        else: bool_str = bool_str + '擁有(沒過)'
            
        if bool_not:bool_str = bool_str + '沒有(過)'
        else: bool_str = bool_str + '沒有(沒過)'
                
        if bool_author : bool_str = bool_str + '作者(過)'
        else: bool_str =bool_str + '作者(沒過)'
            
        if bool_push :bool_str = bool_str + '按讚數(過)'
        else : bool_str = bool_str + '按讚數(沒過)'
                
        if bool_cmt : bool_str = bool_str + '評論(過)'
        else : bool_str = bool_str + '評論(沒過)'
            
        if bool_has and bool_not and bool_author and bool_push and bool_cmt:
            print bool_str#R暫時 
            return True
        else:
            print bool_str#R暫時 
            return False
        
        
    except Exception as ex:
        print 'have error in compare_rules()'+ex



"""
purpose:把規則讀取出來變成一個dict

input:

rules_path:規則檔案的路徑，預設是當下目錄的　./rules.json檔案。存取格式限json。

output:整理好的dict資訊

"""

def load_rules(rules_path = './1.json' ):
    
    try:

        load_rules = {}
        load_rules['path'] = rules_path.replace('1.json','')

        #讀取規則
        with open(rules_path, 'r') as f:
            rules = json.load(f)

        load_rules['recent_page'] = rules['recent_page'] #要爬取的頁數

        has_rules = rules['has'] #符合的條件
        load_rules['has_title'] = has_rules['title']
        load_rules['has_content'] = has_rules['content']

        not_rules = rules['not'] #不符合的條件
        load_rules['not_title'] = not_rules['title']
        load_rules['not_content'] = not_rules['content']

        comment = rules['comment'] #符合推文的內容
        load_rules['comment_content'] = comment['content']

        load_rules['push_count'] = rules['push_count'] #推文數
        load_rules['author'] = rules['author']

        return load_rules
    
    except Exception as ex:
        print 'have error in load_rules()'+ex
        
#　跑迴圈，只要ｌｉｓｔ某一元素，符合對照的部分或全部，回傳Ｔｒｕｅ
#　例如　老狗子愛我（對照）　→　['老狗','子愛我','狗子']　以下ｌｉｓｔ全部都有符合，
#　但程式碼只要一個符合便停止迴圈，以降低不必要的資源浪費
"""
purpose:讓每個規則都跟該文章的屬性對照，僅要有個符合則回傳True，反之

list_compare:從json檔抽出來的list

str_compare:該篇文章性質


"""

def list_look_for(list_compare,str_compare):
    
    try:
        
        result = False
        for i in list_compare:
            if  i in str_compare: #其中某一個只要符合　則 result = True 並跳出迴圈
                result = True
                break 
        return result
    
    except Exception as ex:
        print 'have error in list_look_for()'+ex 





#解析全部的元素
def catch_info(article):
    
    try:
        
        from bs4 import BeautifulSoup
        import re

        PPT_URL='https://www.ptt.cc'
        url = article['href']
        dom = get_web_page(PPT_URL+url)
        soup = BeautifulSoup(dom,'html.parser') #用html.parser引擎
        info = soup.find_all('span',{'class': 'article-meta-value'})

        #基本資訊
        article['author'] = info[0].text.split(' (')[0]
        article['board_name'] = info[1].text
        #標題解析已經有了　title = info[2].text
        article['time'] = info[3].text
        article['content'] = soup.text.split(article['time'])[1].split(url)[0]+url
        article['comment'] = soup.text.split(article['time'])[1].split(url)[1].split('function(e,t,r,n,c,h,o)')[0].replace('\n\n','') #後面兩個\n\n是因為空白無法替除，用兩個換行則取代掉為暫時替代
        return article
    
    except Exception as ex:
        print 'have error in catch_info()'+ex 
        
def save_text(article,path = './'):
    
    import requests
    from bs4 import BeautifulSoup 
    
    month = {'Jan':'1',"Feb":'2',"Mar":'3',"Apr":'4',
             "May":'5',"Jun":'6',"Jul":'7',"Aug":'8',
             "Sep":'9',"Oct":'10',"Nov":'11',"Dec":'12'}

    PPT_URL='https://www.ptt.cc'
    LT = article['time'].split(' ')
    if '' in  LT : del LT[2] # 這裡因為個''(空白)會加入list，在不影響上游程式碼狀況下，這邊直接做處理
        
    time_str = LT[4]+'-'+ month[LT[1]] + '-' + LT[2]  #　年　+　月　+　日
    author_str = article['author'] # 作者
    url_str = article['href'].split('/')[-1].replace('.html','') # 文章編號
    file_name = time_str + '_' + author_str + "_" + url_str + '.txt'
    
    url = article['href']    
    dom = get_web_page(PPT_URL+url) #　取出內文
    soup = BeautifulSoup(dom, 'lxml')
    info_text = soup.find('div',{'id':'main-content'}).text
    with open(path+file_name, "w",encoding='utf8') as text_file:
        text_file.write(info_text)

    