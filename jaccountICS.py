# -*- coding: UTF-8 -*-
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import requests
import pytesseract
import time
import datetime
import os
from tkinter import *
from tkinter import ttk
import re
import uuid
import tkinter.font as tkFont
import platform
import subprocess
import getpass

from PIL import Image, ImageEnhance  # 引用库的顺序

titles = []
times = []
zooms = []
pwds = []
urls = []
clock = []
weeks = []
STARTINGDATE = [2020, 3, 2]
days = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
timeh = [19, 8, 9, 10, 11, 12, 12, 14, 15, 16, 17, 18, 19]
timem = [26, 0, 40, 0, 40, 00, 55, 00, 40, 00, 40, 00, 40]

url = "http://kbcx.sjtu.edu.cn/jaccountlogin"
captcha_url = "https://jaccount.sjtu.edu.cn/jaccount/captcha"
username = 'xia.xh'
pwd = '********'


print("\nWelcome to use the automated jAccount Classtable grabber!\n")
print("Running on", platform.system(), 'operating system.\n')
print("This program only grabs SJTU 2019-2020-Spring Online Courses, converts them into zoom urls",end=' ')
print("and makes an \".ics\" file for calendars while users checking the classtable within program.")
print("Could be quite useful in online learning :P\n")
print("You can also intergrate your own jAccount password into this program.\n")
print("If you need to use it in other semesters, please revise it yourself.  \n")
print("You may download the driver from https://sites.google.com/a/chromium.org/chromedriver/home if a problem occured.\n")
print("Please confirm the starting date of the semester:",STARTINGDATE)
print("\nEnjoy  :)\n")


def getCaptcha(captcha_url, cookies, params):# 获取验证码

    response = requests.get(captcha_url, cookies=cookies, params=params)
    with open('img.jpeg', 'wb+') as f:
        f.writelines(response)
    image = Image.open('img.jpeg')
    image = image.convert('L')
    image = ImageEnhance.Contrast(image)
    image = image.enhance(3)
    image2 = Image.new('RGB', (150, 60), (255, 255, 255))
    image2.paste(image.copy(), (25, 10))
    image2.save("img2.jpeg")
    code = pytesseract.image_to_string(image2)
    code.replace(" ", "")
    return code


def getClasses():# 抓取课程信息

    chrome_driver.get(url)

    while(("jaccount" in chrome_driver.current_url)):  # 防止验证码识别错误，重复尝试。
        cookies = chrome_driver.get_cookies()
        cookies = {i["name"]: i["value"] for i in cookies}
        uuid = chrome_driver.find_element_by_xpath(
            '//form/input[@name="uuid"]')
        params = {
            'uuid': uuid.get_attribute('value')
        }

        code = ""
        while(code == ""):
            code = getCaptcha(captcha_url, cookies, params)
            print("\ncode =", code)
            print()
            time.sleep(0.03)

        input_user = chrome_driver.find_element_by_id('user')
        input_user.send_keys(username)
        input_pass = chrome_driver.find_element_by_id('pass')
        input_pass.send_keys(pwd)
        input_code = chrome_driver.find_element_by_id('captcha')
        input_code.send_keys(code)
        input_code.send_keys(Keys.ENTER)
        # print(chrome_driver.current_url)
        time.sleep(0.03)
        warnings=chrome_driver.find_elements_by_id('div_warn')
        if(len(warnings)>0):
            warnings[0]=warnings[0].text
            print (warnings[0])
            if(warnings[0]=="wrong username or password" or "用户名和密码" in str(warnings[0])):
                print("\nWrong username or password! Please check!")
                sys.exit()

    chrome_driver.get(
        "http://kbcx.sjtu.edu.cn/kbcx/xskbcx_cxXskbcxIndex.html?gnmkdm=N2151&layout=default")
    time.sleep(1)
    #print(chrome_driver.find_elements_by_class_name("timetable_con text-left"))
    classes = chrome_driver.find_elements_by_css_selector('td.td_wrap')
    return classes
    #times = chrome_driver.find_elements_by_css_selector('span.节/周')
    #zooms = chrome_driver.find_elements_by_css_selector('span.title')


def drawClass(c, wk, wkday, st, ed, txt, url): # 对每一个课程对象进行绘制

    print("Drawing", txt, " on", c, "at Day", wkday, "From", st, "to", ed)
    wkday = int(wkday)
    st = int(st)
    ed = int(ed)
    zuo = 100
    you = 48
    x0 = -5
    y0 = 50
    c.create_rectangle(x0+20+(wkday-1)*zuo, y0+20+(st-1)*you,
                       x0+100+(wkday-1)*zuo, y0+53+(ed-1)*you, tags="#1")
    c.create_text(2+x0+20+(wkday-1)*zuo, 10+y0+20+(st-1)*you, text=re.sub("[\(,\),（,）]","",txt), anchor=NW)  # 正则表达式 中文括号，特别小心


class Event:    # 日历事件类

    def __init__(self, kwargs):

        self.event_data = kwargs

    def __turn_to_string__(self):

        self.event_text = "BEGIN:VEVENT\n"
        for item, data in self.event_data.items():
            item = str(item).replace("_", "-")
            if item not in ["ORGANIZER", "DTSTART", "DTEND"]:
                self.event_text += "%s:%s\n" % (item, data)
            else:
                self.event_text += "%s;%s\n" % (item, data)
        self.event_text += "END:VEVENT\n"
        return self.event_text


def drawWk(): # 绘制整版课表大框架搭建

    top = Tk()
    top.geometry('630x700')
    top.title("jAccount ClassTable")
    c = Canvas(top, width=500, height=1000, bg='white')
    c.pack()

    lis = []
    for i in range(len(titles)+1):
        lis.append(i)
    lis[0]="Please select WEEK:"

    x = StringVar()     # 创建变量，便于取值
    com = ttk.Combobox(top, textvariable=x)     # 创建下拉菜单
    com.place(x=10, y=15)     # 将下拉菜单绑定到窗体
    com["value"] = lis    # 给下拉菜单设定值
    com.current(0)

    def xFunc(event):
        if (x.get()!="Please select WEEK:"):
            week = x.get()
            # com.destroy()
            print()
            c.delete(ALL)  # 每次更新刷新
            ft2 = tkFont.Font(font=('Fixdsys', '26', tkFont.NORMAL), size=40)
            l = Label(top, text="WEEK "+week+"      ", font=ft2)
            l.place(x=270, y=15)
            drawWeek(c, week, drawClass)

    com.bind("<<ComboboxSelected>>", xFunc)

    top.mainloop()


def drawWeek(c, week, fun): # 绘制整版课表 对每堂课判定是否绘制
                            # 生成ics文件 对每堂课判定是否绘制

    print("WEEK: ",week)
    for i in range(len(titles)):
        # print("WEEK: ",week)
        if (int(clock[i][2]) <= int(week) and int(clock[i][3]) >= int(week)):
            # print (i,clock[i][4])
            # if(clock[i][4]==1 and week%2==1):
            if(clock[i][4] == 1 and int(week) % 2 == 1):
                # print(i)
                fun(c, week, weeks[i][0], clock[i][0],
                    clock[i][1], titles[i], urls[i])
            if(clock[i][4] == 2 and int(week) % 2 == 0):
                # print(i)
                fun(c, week, weeks[i][0], clock[i][0],
                    clock[i][1], titles[i], urls[i])
            if(int(clock[i][4]) == 0):
                # print(i)
                fun(c, week, weeks[i][0], clock[i][0],
                    clock[i][1], titles[i], urls[i])


class Calendar: # 日历类

    def __init__(self, calendar_name="My Calendar"):
        self.__events__ = {}
        self.__event_id__ = 0
        self.calendar_name = calendar_name

    def add_event(self, **kwargs):
        event = Event(kwargs)
        event_id = self.__event_id__
        self.__events__[self.__event_id__] = event
        self.__event_id__ += 1
        return event_id

    def modify_event(self, event_id, **kwargs):
        for item, data in kwargs.items():
            self.__events__[event_id].event_data[item] = data

    def remove_event(self, event_id):
        self.__events__.pop(event_id)

    def get_ics_text(self):
        self.__calendar_text__ = """BEGIN:VCALENDAR\nPRODID:-//Apple Inc.//Mac OS X 10.14.6//EN\nX-APPLE-CALENDAR-COLOR:#FD97E4\nVERSION:2.0\nCALSCALE:GREGORIAN\nMETHOD:PUBLISH\nX-WR-CALNAME:%s\nX-WR-TIMEZONE:Asia/Shanghai\nCALSCALE:GREGORIAN\n""" % self.calendar_name
        for key, value in self.__events__.items():
            self.__calendar_text__ += value.__turn_to_string__()
        self.__calendar_text__ += "END:VCALENDAR"
        return self.__calendar_text__

    def save_as_ics_file(self):
        ics_text = self.get_ics_text()
        open("%s.ics" % self.calendar_name, "w", encoding="utf8").write(
            ics_text)  # 使用utf8编码生成ics文件
        print ("\n\nCalendar file successfully exported at:",os.getcwd()+"/"+"%s.ics !\n" % self.calendar_name)

    def open_ics_file(self):
        os.system("%s.ics" % self.calendar_name)


def add_event(cal, SUMMARY, DTSTART, DTEND, DESCRIPTION, LOCATION): # 增加事件函数
    """
    :param cal: calender
    :param SUMMARY:
    :param DTSTART:
    :param DTEND:
    :param DESCRIPTION:
    :param LOCATION:
    :return:
    """
    time_format = "TZID=Asia/Shanghai:{date.year}{date.month:0>2d}{date.day:0>2d}T{date.hour:0>2d}{date.minute:0>2d}00"
    dt_start = time_format.format(date=DTSTART)
    dt_end = time_format.format(date=DTEND)
    create_time = datetime.datetime.today().strftime("%Y%m%dT%H%M%SZ")
    cal.add_event(
        SUMMARY=SUMMARY,
        ORGANIZER="CN=My Calendar:mailto:developer@sjtu.edu.cn",
        DTSTART=dt_start,
        DTEND=dt_end,
        DTSTAMP=create_time,
        UID=str(uuid.uuid5(uuid.NAMESPACE_DNS, dt_start+SUMMARY +
                           create_time))+"-uuid@sjtu.edu.cn",  # 生成唯一UUID
        SEQUENCE="0",
        CREATED=create_time,
        DESCRIPTION=DESCRIPTION,
        LAST_MODIFIED=create_time,
        LOCATION=LOCATION,
        STATUS="CONFIRMED",
        TRANSP="OPAQUE"
    )


def wktoday(wk, wkday): # 输入周数和第几天，输出日期。

    year = int(STARTINGDATE[0])
    month = int(STARTINGDATE[1])
    day = int(STARTINGDATE[2])
    day = int(day)+(int(wk)-1)*7+int(wkday)-1
    if ((year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)):
        days[2] = 29
    while(day > days[month]):
        day = day-days[month]
        month = month+1
    while(month > 12):
        year = year+1
        month = month-12
    return year, month, day


def getprecTime(at): # 对每堂课的时间节点获取精确的时和分
    return timeh[at], timem[at]


def gnrtICS(c, wk, wkday, st, ed, txt, url): # 对一节课增加对应的一项事件

    print("PRINTING ICS:", txt, "  at Week", wk,
          "Day", wkday, ", from Class", st, "to", ed)
    date = wktoday(wk, wkday)
    pTime0 = getprecTime(int(st))
    pTime1 = getprecTime(int(ed))
    add_event(calendar,
              SUMMARY=txt,
              DTSTART=datetime.datetime(
                  year=date[0], month=date[1], day=date[2], hour=pTime0[0], minute=pTime0[1], second=00),
              DTEND=datetime.datetime(
                  year=date[0], month=date[1], day=date[2], hour=pTime1[0], minute=pTime1[1], second=00),
              DESCRIPTION=url,
              LOCATION=url
              )


def printALLICS(): # 生成ICS文件大框架函数

    lis = []
    c = 0
    for i in range(len(titles)):
        lis.append(i+1)
    for i in lis:
        drawWeek(c, i, gnrtICS)
    calendar.save_as_ics_file()


def extractClasses(): # 对获取到的所有课程 过滤筛选 得到数个列表

    classes = getClasses()
    for i in range(len(classes)):
        # print (classes[i].text)
        if (classes[i].text != ""):
            tmp1 = classes[i].text 
            tmp0 = tmp1.split()
            if (tmp0[6] != '暂不开课'):
                print(tmp0)
                # print(classes[i].get_attribute('id'))
                weeks.append(re.findall(
                    r"\d+\.?\d*", classes[i].get_attribute('id')))
                print(weeks[-1])
                titles.append(tmp0[0])
                times.append(tmp0[1])
                tmp2 = re.findall(r"\d+\.?\d*", tmp0[6])  # 正则表达式
                if(len(tmp2) > 0):
                    if (len(tmp2) > 1):  # 有两种类型
                        pwds.append(str(tmp2[1]))
                        zooms.append(str(tmp2[0]))
                    else:
                        # print(tmp2)
                        zooms.append(tmp2[0])
                        pwds.append(re.findall(r"\d+\.?\d*", tmp0[7])[0])
                else:
                    zooms.append("NOT PROVIDED")
                    pwds.append("NOT PROVIDED")
                urls.append("NOT PROVIDED")

                if (zooms[-1] != "NOT PROVIDED"):
                    urls[-1] = "https://zoom.com.cn/j/" + \
                        zooms[-1]+"?pwd="+pwds[-1]
                # print (titles[-1],times[-1],zooms[-1],pwds[-1],urls[-1])
                print(titles[-1], urls[-1])

            #print (tmp0[5])
            # print()

                clock.append(re.findall(r"\d+\.?\d*", times[-1]))
                clock[-1].append(0)
                if ("单" in times[-1]):
                    clock[-1][-1] = 1
                if ("双" in times[-1]):
                    clock[-1][-1] = 2
                print(clock[-1])

                # print(len(titles),len(times),len(zooms),len(pwds),len(urls),len(clock))

                print("")


if __name__ == '__main__': # 主程序

    try:

        if(pwd == '********'): # 更新用户名密码
            username = input("Please enter your USERNAME: ")
            pwd = getpass.getpass('Please enter your PASSWORD: ') # 密码不可见
            # pwd = input("Please enter your PASSWORD:")
        else:
            print("Sleeping for 2 secs.")
            time.sleep(2)

        calendar = Calendar(calendar_name="2020-Spring{auto}")
        option = webdriver.ChromeOptions()
        option.add_argument('disable-infobars')
        if (platform.system() == "Darwin"):
            chrome_driver = webdriver.Chrome("./chromedriver")
        if (platform.system() == "Windows"):
            chrome_driver = webdriver.Chrome("./chromedriver.exe")
            pytesseract.pytesseract.tesseract_cmd = 'C:\Program Files\Tesseract-OCR\\tesseract.exe'
        if (platform.system() == "Linux"):
            chrome_driver = webdriver.Chrome("./chromedriver_linux")  # 判断操作系统 根据操作系统自动选择驱动程序

        extractClasses() # 提取课程
        chrome_driver.close() # 关闭浏览器窗口
        printALLICS() # 打印ICS文件
        drawWk() # 绘制课表

        # print(chrome_driver.find_elements(By.CLASS_NAME,"timetable_con text-left"))
        # chrome_driver.close()
        # print(chrome_driver.page_source)
        # print (os.getcwd()+"/2020-Spring{auto}.ics")
        print('\nSucceeded!')

        if (platform.system() == "Darwin"):
            print("\nOpening the calendar for you........")
            time.sleep(1)
            subprocess.call(["open", "2020-Spring{auto}.ics"])  # 自动打开！

    except:
        try:
            chrome_driver.close()
        except:
            time.sleep(0.1)
        print("\n\nUnexpectedly halted! Please try again.") # 故障处理
