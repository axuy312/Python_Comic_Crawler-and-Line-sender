from bs4 import BeautifulSoup
from selenium import webdriver
from opencc import OpenCC
import numpy as np
import sqlite3 as lite
import tkinter as tk
import requests, re, time, os, shutil, pandas, time

selSeries = ''
token_index = 0
tokens = [
 #請在此加入申請好的LINE Token   
]

tokens_size = len(tokens)
#print("size: "+str(tokens_size))

# Init
headers = {'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh-CN;q=0.7,zh;q=0.6'}

urlBase = 'https://www.manhuaren.com'
url = 'https://www.manhuaren.com/manhua-haizeiwang-onepiece/?from=/manhua-list/'
res = requests.get(url, headers = headers)
soup = BeautifulSoup(res.text, 'lxml')
liList = soup.findAll("a",{"class":"chapteritem"})
comic_title = OpenCC('s2twp').convert(soup.findAll("p",{"class":"detail-main-info-title"})[0].text)

#-------------------

def check_comics():
    # 檢查資料庫最新的漫畫集數
    global comic_title
    global url
    global urlBase
    with lite.connect('./sqlite/'+comic_title+'.sqlite') as db:
        dbCheck = pandas.read_sql_query('select "series-tw", "series-cn" from comics', con = db)

    datas = []
    with lite.connect('./sqlite/'+comic_title+'.sqlite') as db:
        datas = pandas.read_sql_query('select "series-tw", "series-cn", link from comics', con = db)
  
    #print(datas)
    
    
    # 利用網路爬蟲檢查網路上最新的集數
    headers = {'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh-CN;q=0.7,zh;q=0.6'}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'lxml')
    new_comics = []
    comic_title = OpenCC('s2twp').convert(soup.findAll("p",{"class":"detail-main-info-title"})[0].text)
    for rec in soup.findAll('a', {'class', 'chapteritem'}):
        title_ch = rec.text
        title_tw = OpenCC('s2twp').convert(title_ch)
        if not (title_tw in dbCheck.values):
            new_comics.append([title_tw, title_ch,urlBase+rec.get('href')])
            print("新增"+title_tw)
    new_comics.reverse()
     
    if not(new_comics == []):
        comics = np.append(datas.values,np.array(new_comics),0)
        comic_df = pandas.DataFrame(comics, columns = ['series-tw', 'series-ch', 'link'])
        with lite.connect('./sqlite/'+comic_title+'.sqlite') as db:
            comic_df.to_sql('comics', con = db, if_exists='replace')
    #print(new_comics)
    
    return new_comics

def getImgLink(link):
    driver = webdriver.Chrome('C:\\Users\\axuy312\\Anaconda_BigData\\高階驗證碼\\driver\\chromedriver.exe')
    driver.get(link)
    imgLinks = []
    eles = driver.find_elements_by_class_name('lazy')
    for e in eles:
        imgLinks.append(e.get_attribute('src'))
    #print(imgLink)
    driver.close()
    return imgLinks

def getComic(link, series):
    global comic_title
    headers = {'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh-CN;q=0.7,zh;q=0.6'}
    res = requests.get(link, headers=headers)
    #print(res.text)
    
    print('更新中....')
    soup = BeautifulSoup(res.text, 'lxml')
    scriptList = soup.findAll("script")
    
    cnt = 0
    MaxCnt = 0
    Max = 0
    parseString = ''
    for script in scriptList:
        string = script.find(text=True, recursive=False)
        if not(string == None) and len(string) > Max:
            Max = len(string)
            MaxCnt = cnt
            parseString = string
        cnt = cnt + 1
    initLinks = getImgLink(link)
    
    page_code = []
    for iLink in initLinks:
        s = re.findall(r"[0-9]*_[0-9]*", iLink)
        tmp = s[0].split('_')
        page_code.append((int(tmp[0]), int(tmp[1])))
    
    
    #print(parseString+"\n")
    #string1 = re.findall("m=.*", parseString)
    #print(string1)
    #print("\n")
    #if string1:
    string1 = re.findall("[0-9]*_[0-9]*", parseString)
    #print(string1)
    for s in string1:
        tmp = s.split('_')
        page_code.append((int(tmp[0]), int(tmp[1])))
    page_code = sorted(page_code)
    page_link = []
    page_link_tmp = []
    for code in page_code:
        page_link_tmp.append((str(code[0])+'_'+str(code[1])))
    
    index = 0
    
    if page_link_tmp:
        page_link.append(page_link_tmp[0])
    for p in page_link_tmp:
        if not page_link[index] == p:
            page_link.append(p)
            index = index + 1
    
    #print(np.array(page_link_tmp))
    print(np.array(page_link))
    
    path = "./Comics"
    if not os.path.isdir(path):
        os.mkdir(path)
    
    path = path + "/" + comic_title
    if not os.path.isdir(path):
        os.mkdir(path)

    path = path + "/" + series + "/"
    if not os.path.isdir(path):
        os.mkdir(path)
    
    
    
    
    print('正在下載....')
    for code in page_link:
        #print(code)
        #print(re.sub(r"[0-9]*_[0-9]*", code, initLink))
        imgUrl = re.sub(r"[0-9]*_[0-9]*", code, initLinks[0])
        imgRes = requests.get(imgUrl, headers=headers)
        if imgRes.reason == 'Not Found':
            if re.findall(r'\.jpg', imgUrl):
                print("檔案格式更換 (jpg -> png)")
                imgUrl = re.sub(r"\.jpg", ".png", imgUrl)
            elif re.findall(r'\.png', imgUrl):
                print("檔案格式更換 (png -> jpg)")
                imgUrl = re.sub(r"\.png", ".jpg", imgUrl)
            else:
                print('抓不到檔案格式')
            imgRes = requests.get(imgUrl, headers=headers)
            if not imgRes.reason == 'OK':
                print("檔案爬不到( At getComic(link, series) "+comic_title+"/"+series+"/"+code+" URL: "+ imgUrl+" )")
        with open(path+code.split('_')[0]+'.jpg', 'wb') as f:
            f.write(imgRes.content)
        time.sleep(1)
    print('完成')

def send_comic_page(fileAry):
    global token_index
    global tokens
    global tokens_size
    global selSeries
    
    headers = {
        'Authorization': 'Bearer '+tokens[token_index]
    }

    payload = {
     'message':selSeries, 
    }
    
    res = requests.post('https://notify-api.line.me/api/notify', data = payload, headers = headers)
    print(res.json())
    page_cnt=1
    for f in fileAry:
        files = {
            'imageFile': open(f, 'rb')
        }
        print('正在寄送'+f)
        payload = {
         'message':'第'+str(page_cnt)+'頁', 
        }
        res = requests.post('https://notify-api.line.me/api/notify', data = payload, files=files, headers = headers)
        page_cnt = page_cnt + 1
        time.sleep(1)
        tmpToken = token_index
        while res.json()['message'] == 'Image rate limit exceeded.':
            new_tkn = (token_index + 1) % tokens_size
            print("Token更換: "+tokens[token_index]+" -> "+ tokens[new_tkn])
            token_index = new_tkn
            if token_index == tmpToken:
                print('所有Token皆暫時無法使用!')
                return
            headers = {
                'Authorization': 'Bearer '+tokens[token_index]
            }
            res = requests.post('https://notify-api.line.me/api/notify', data = payload, files=files, headers = headers)


def send_comics(s):
    global comic_title
    exist = False
    with lite.connect('./sqlite/'+comic_title+'.sqlite') as db:
        allData = pandas.read_sql_query('select * from comics', con = db)
        #print(allData)
        exist = s in allData.values
    if(exist):
        path = './Comics/'+comic_title+'/'+s+'/'
        if not os.path.isdir(path):
            with lite.connect('./sqlite/'+comic_title+'.sqlite') as db:
                sel = pandas.read_sql_query('select "series-tw", "series-cn","link" from comics where "series-tw" = "'+s+'" or "series-cn" = "'+s+'"', con = db)
            getComic(sel['link'][0], sel['series-tw'][0])
        ary = []
        for f in os.listdir(path):
            ary.append(int(f.replace('.jpg', '')))
        ary.sort()
        fileAry = []
        print(ary)
        for c in ary:
            #print('{}/{}.jpg'.format(path,c))
            fileAry.append(path+str(c)+'.jpg')
        send_comic_page(fileAry)
    else:
        print(s+"找不到( At send_comics() )")
    

#check_comics()
        

send_comics('第987話')

print('結束')
