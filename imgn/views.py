from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from settings.update_json import *
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from imgn.make_timetable import *
from PIL import ImageColor
from imgn.media_json import *
from urllib import parse
import numpy as np
import time
import os
from django.contrib.auth.models import User
#-------------------- for text preview -------------------
from PIL import Image, ImageFont, ImageDraw
#---------------------------------------------------------
#from django.utils import simplejson
# Create your views here.

def imgn(request):  # 페이지 로딩시 리스트에 이미지, 문자 올림
    img_list = img_list_in_bucket(user_id)  # 버켓안에 최신파일 이름 받아옴
    print("현재 저장된 이미지 목록->")
    print(img_list) # 저장된 이미지 리스트
    img_time_list = []
    img_name_list = []
    text_time_list = []
    text_name_list = []

    for i in range(len(img_list)): # img_list에서 시간이랑 이미지 이름 분리
        len_t = int(img_list[i][14]) # (지속시간 길이)
        img_time_list.append(str(img_list[i][15: 14 + len_t+1])) # 파일 이름 앞에 지속시간 분리 (첫자리 제외)
        img_name_list.append(str(img_list[i][14 + len_t+1:])) # 나머지 파일이름 따로 저장

    text_list = text_list_in_bucket(user_id)
    for i in range(len(text_list)):
        len_t = int(text_list[i][14]) # (지속시간 길이)
        text_time_list.append(str(text_list[i][15: 14 + len_t+1])) # 파일 이름 앞에 지속시간 분리 (첫자리 제외)
        text_name_list.append(str(text_list[i][14 + len_t+1:])) # 나머지 파일이름 따로 저장

    print("현재 저장된 문자 목록->")
    print(text_list) # 저장된 문자 리스트


    list_dict = {
        'img_name' : img_name_list,
        'img_time' : img_time_list,
        'text_name' : text_name_list,
        'text_time' : text_time_list,
    }

    context = json.dumps(list_dict)
    userinfo = User.objects.get(username=request.user.username)
    return render(request, 'image.html', {'context': context, 'userinfo':userinfo})

@csrf_exempt
def upload_img(request):
    print("호출 성공")
    if request.method == 'POST':
        if request.is_ajax():

            stay_time = request.POST['time']    # 지속시간
            img_name = request.POST['img_name']  # 이미지 이름
            print(stay_time)
            img = request.FILES.get('img')  # 이미지를 request에서 받아옴
            path = default_storage.save(user_id +"/img.jpg", ContentFile(img.read()))
            now_kst = time_now()
            UPLOAD("ynumcl-act", user_id + "/img.jpg", user_id + "/IMAGE/" + now_kst.strftime("%Y%m%d%H%M%S") + str(len(stay_time)) + str(stay_time) + img_name)
            os.remove(user_id+"/img.jpg") # 장고에서 중복된 이름의 파일에는 임의로 이름을 변경하기 때문에 임시파일은 제거
            return redirect('image.html')
        else:
            print("ajax 통신 실패!")
            return redirect('image.html')
    else:
        print("POST 호출 실패!")
        return redirect('image.html')

@csrf_exempt
def save_letter(request): # 문자 설정 -> 확인 버튼 눌렀을 시 // 버켓 안 TEXT_LIST 디렉토리에 업로드하여 저장 (TIMETABLE을)
    if request != "":
        print("========= 시작 ===========")

        change = request_body_list_text(request.body)
        change[9] = parse.unquote(change[9])

        data = make_Timetable_text()
        now_kst = time_now()  # 현재시간 받아옴
        now_kst1 = time_now()
        now_kst = now_kst + timedelta(seconds=15)

        data[4]["detail_info"]["x"] = str(change[1])
        data[4]["detail_info"]["y"] = str(change[2])
        data[4]["detail_info"]["width"] = str(change[3])
        data[4]["detail_info"]["height"] = str(change[4])
        data[4]["detail_info"]["play_speed"] = str(change[5])
        data[4]["detail_info"]["play_count"] = str(change[6])
        data[4]["detail_info"]["font_size"] = "64"     # 폰트사이즈 - 인터페이스 수정 전까지 고정시킴
        data[4]["detail_info"]["scroll_fix"] = str(change[10])
        data[4]["detail_info"]["play_second"] = str(change[11])
        data[4]["title"] = str(change[0])
        hex = str("#" + change[8])
        rgb_value = ImageColor.getcolor(hex,"RGB")
        data[4]["detail_info"]["red_green_blue"] = str(rgb_value)

        data[4]["time"]["year"] = now_kst.strftime("%Y").zfill(4)
        data[4]["time"]["month"] = now_kst.strftime("%m").zfill(2)
        data[4]["time"]["day"] = now_kst.strftime("%d").zfill(2)
        data[4]["time"]["hour"] = now_kst.strftime("%H").zfill(2)
        data[4]["time"]["minute"] = now_kst.strftime("%M").zfill(2)
        data[4]["time"]["second"] = now_kst.strftime("%S").zfill(2)

        if (str(change[10]) == '0'):
            title = str(change[0])
            len_text = len(title)
            all_text_pixel = int(0.9 * int(len_text) * int(data[4]["detail_info"]["font_size"])) - int(change[3])
            micro_second = (all_text_pixel * 100) / int(change[5]) # 100 is ms
            ans = int(np.rint((micro_second / 1000) * int(change[6])))
            now_kst = now_kst + timedelta(seconds=15) + timedelta(seconds=ans)
            time_code = str(len(str(ans))) + str(ans)
        elif (str(change[10]) == '1'):
            now_kst = now_kst + timedelta(seconds=15) + timedelta(seconds=(int(change[11])))
            time_code = str(len(str(change[11]))) + str(change[11])
        else:
            print("스크롤-고정 선택 오류")
            return redirect('image.html')

        createDirectory(user_id)
        save_file(data)
        UPLOAD("ynumcl-act", user_id+"/send" , user_id + "/JSON/TEXT_LIST/" + now_kst1.strftime("%Y%m%d%H%M%S") + time_code + str(change[9]))

        return redirect('image.html')
    else:
        return redirect('image.html')

@csrf_exempt
def edit_letter(request): # 문자편집
    if request != "":
        print("========= 시작 ===========")
        text_name_list = []
        text_list = text_list_in_bucket(user_id)
        for i in range(len(text_list)):
            len_t = int(text_list[i][14])  # (지속시간 길이)
            text_name_list.append(str(text_list[i][14 + len_t + 1:]))  # 나머지 파일이름 따로 저장

        change = request_body_list_text(request.body)
        change[9] = parse.unquote(change[9])

        index = int(change[12])
        exiting_time = text_list[index][:-len(text_name_list[index])]

        data = make_Timetable_text()
        now_kst = time_now()  # 현재시간 받아옴

        now_kst = now_kst + timedelta(seconds=15)

        data[4]["detail_info"]["x"] = str(change[1])
        data[4]["detail_info"]["y"] = str(change[2])
        data[4]["detail_info"]["width"] = str(change[3])
        data[4]["detail_info"]["height"] = str(change[4])
        data[4]["detail_info"]["play_speed"] = str(change[5])
        data[4]["detail_info"]["play_count"] = str(change[6])
        data[4]["detail_info"]["font_size"] = "64"     # 폰트사이즈 - 인터페이스 수정 전까지 고정시킴
        data[4]["detail_info"]["scroll_fix"] = str(change[10])
        data[4]["detail_info"]["play_second"] = str(change[11])
        data[4]["title"] = str(change[0])
        hex = str("#" + change[8])
        rgb_value = ImageColor.getcolor(hex,"RGB")
        data[4]["detail_info"]["red_green_blue"] = str(rgb_value)

        data[4]["time"]["year"] = now_kst.strftime("%Y").zfill(4)
        data[4]["time"]["month"] = now_kst.strftime("%m").zfill(2)
        data[4]["time"]["day"] = now_kst.strftime("%d").zfill(2)
        data[4]["time"]["hour"] = now_kst.strftime("%H").zfill(2)
        data[4]["time"]["minute"] = now_kst.strftime("%M").zfill(2)
        data[4]["time"]["second"] = now_kst.strftime("%S").zfill(2)

        createDirectory(user_id)
        save_file(data)
        UPLOAD("ynumcl-act", user_id+"/send" , user_id + "/JSON/TEXT_LIST/" + exiting_time + str(change[9]))

        return redirect('image.html')
    else:
        return redirect('image.html')


@csrf_exempt
def event_trans(request):    # 이벤트 전송 버튼 TEXT_LIST에서 선택된 TIMETABLE을 JSON/TIMETABLE로 전송
    check_list_text = value_of_request_body_list(request.body) # 선택된 파일 인덱스
    blobs = storage_client.list_blobs("ynumcl-act")
    ############ 이미지 정보 ############
    list_blob_img = []
    list_blob_text = []
    except_str = str(user_id + "/IMAGE/")  # 제외시킬 문자열
    except_str1 = str(user_id + "/JSON/TEXT_LIST/")  # 제외시킬 문자열
    for blob in blobs:
        if blob.name.startswith(except_str):
            blob.name = blob.name.replace(except_str, '')
            list_blob_img.append(blob.name)
        if blob.name.startswith(except_str1):
            blob.name = blob.name.replace(except_str1, '')
            list_blob_text.append(blob.name)
    if (len(list_blob_img)) >= 2:
        list_blob_img.pop(0)
    if (len(list_blob_text)) >= 2:
        list_blob_text.pop(0)

    call_text = []  # TEXT_LIST에서 선택된 문자를 담을 리스트
    call_img = []
    for index in range(40):
        if index < 20:  # 문자
            if check_list_text[index] != '':  # 체크된 인덱스
                if len(list_blob_text) > (index):  # 이미 업로드된 범위 내의 체크
                    call_text.append(list_blob_text[index])
                else:
                    pass
        else: # 이미지
            if check_list_text[index] != '':  # 체크된 인덱스
                if len(list_blob_img) > (index-20):  # 이미 업로드된 범위 내의 체크
                    call_img.append((list_blob_img[index-20]))
                else:
                    pass

    data = []
    now_kst = time_now()  # 현재시간 받아옴
    now_kst = now_kst + timedelta(seconds=15)
    now_kst1 = time_now()  # 현재시간 받아옴
    cum_time = 0
    sort_time = []

    for i in range(len(call_img)):  # 사진목록의 타임테이블 작성
        now_kst = now_kst + timedelta(seconds= cum_time)
        # 시간 추출 부분
        len_t = int(call_img[i][14])  # (지속시간 길이)
        img_time = (str(call_img[i][15: 14 + len_t + 1]))  # 파일 이름 앞에 지속시간 분리 (첫자리 제외)
        img_name = (str(call_img[i][14 + len_t + 1:]))  # 나머지 파일이름 따로 저장

        # 파일이름만 추가
        info = {}
        info["time"] = {}
        info["time"]["year"] = now_kst.strftime("%Y").zfill(4)
        info["time"]["month"] = now_kst.strftime("%m").zfill(2)
        info["time"]["day"] = now_kst.strftime("%d").zfill(2)
        info["time"]["hour"] = now_kst.strftime("%H").zfill(2)
        info["time"]["minute"] = now_kst.strftime("%M").zfill(2)
        info["time"]["second"] = now_kst.strftime("%S").zfill(2)
        info["time"]["alltime"] = now_kst.strftime("%Y").zfill(4) + now_kst.strftime("%m").zfill(2) + now_kst.strftime(
            "%d").zfill(2) + now_kst.strftime("%H").zfill(2) + now_kst.strftime("%M").zfill(2) + now_kst.strftime(
            "%S").zfill(2)
        sort_time.append(int(info["time"]["alltime"]))
        info["type"] = "image"
        info["action"] = "play"
        info["title"] = str(img_name)
        data.append(info)
        now_kst = now_kst + timedelta(seconds=(int(img_time)))

        info = {}
        info["time"] = {}
        info["time"]["year"] = now_kst.strftime("%Y").zfill(4)
        info["time"]["month"] = now_kst.strftime("%m").zfill(2)
        info["time"]["day"] = now_kst.strftime("%d").zfill(2)
        info["time"]["hour"] = now_kst.strftime("%H").zfill(2)
        info["time"]["minute"] = now_kst.strftime("%M").zfill(2)
        info["time"]["second"] = now_kst.strftime("%S").zfill(2)
        info["time"]["alltime"] = now_kst.strftime("%Y").zfill(4) + now_kst.strftime("%m").zfill(2) + now_kst.strftime(
            "%d").zfill(2) + now_kst.strftime("%H").zfill(2) + now_kst.strftime("%M").zfill(2) + now_kst.strftime(
            "%S").zfill(2)
        sort_time.append(int(info["time"]["alltime"]))
        info["type"] = "image"
        info["action"] = "stop"
        data.append(info)

        cum_time += int(img_time) + 1
        # 해당 이미지 media/image/로 업로드
        copy_blob("ynumcl-act", user_id + "/IMAGE/" + str(call_img[i]), "ynumcl-act",
                  user_id + "/MEDIA/image/" + str(img_name))

    cum_time = 0

    for i in range(len(call_text)):   # 텍스트 부분

        DOWNLOAD("ynumcl-act", user_id + "/JSON/TEXT_LIST/" + call_text[i], user_id + "/temp")
        text_setting = read_json()

        cum_time += 1
        now_kst = now_kst + timedelta(seconds=(int(cum_time)))

        info = {}
        info["time"] = {}
        info["detail_info"] = {}
        info["detail_info"]["x"] = text_setting[4]["detail_info"]["x"]
        info["detail_info"]["y"] = text_setting[4]["detail_info"]["y"]
        info["detail_info"]["width"] = text_setting[4]["detail_info"]["width"]
        info["detail_info"]["height"] = text_setting[4]["detail_info"]["height"]
        info["detail_info"]["scroll_fix"] = text_setting[4]["detail_info"]["scroll_fix"]
        info["detail_info"]["play_speed"] = text_setting[4]["detail_info"]["play_speed"]
        info["detail_info"]["play_count"] = text_setting[4]["detail_info"]["play_count"]
        info["detail_info"]["font_name"] = "NanumGothic"  # 추가필요
        info["detail_info"]["font_size"] = text_setting[4]["detail_info"]["font_size"]
        info["detail_info"]["play_second"] = text_setting[4]["detail_info"]["play_second"]
        info["detail_info"]["thickness_italics"] = "0"  # 추가필요
        info["detail_info"]["red_green_blue"] = text_setting[4]["detail_info"]["red_green_blue"]

        info["time"] = {}
        info["time"]["year"] = now_kst.strftime("%Y").zfill(4)
        info["time"]["month"] = now_kst.strftime("%m").zfill(2)
        info["time"]["day"] = now_kst.strftime("%d").zfill(2)
        info["time"]["hour"] = now_kst.strftime("%H").zfill(2)
        info["time"]["minute"] = now_kst.strftime("%M").zfill(2)
        info["time"]["second"] = now_kst.strftime("%S").zfill(2)
        info["time"]["alltime"] = now_kst.strftime("%Y").zfill(4) + now_kst.strftime("%m").zfill(2) + now_kst.strftime(
            "%d").zfill(2) + now_kst.strftime("%H").zfill(2) + now_kst.strftime("%M").zfill(2) + now_kst.strftime(
            "%S").zfill(2)
        sort_time.append(int(info["time"]["alltime"]))

        info["title"] = text_setting[4]["title"]
        info["type"] = "string"
        info["action"] = "play"
        data.append(info)

        if (str(text_setting[4]["detail_info"]["scroll_fix"]) == '0'):  # 스크롤
            title = str(text_setting[4]["title"])
            len_text = len(title)
            all_text_pixel = int(0.9 * int(len_text) * int(text_setting[4]["detail_info"]["font_size"])) - int(
                text_setting[4]["detail_info"]["width"])
            micro_second = (all_text_pixel * 100) / int(text_setting[4]["detail_info"]["play_speed"])  # 100 is ms
            ans = np.rint((micro_second / 1000) * int(text_setting[4]["detail_info"]["play_count"]))
            now_kst = now_kst + timedelta(seconds=(int(ans))) + timedelta(seconds=1)
            cum_time += (ans + 1)
        elif (str(text_setting[4]["detail_info"]["scroll_fix"]) == '1'):  # 고정
            now_kst = now_kst + timedelta(seconds= (int(text_setting[4]["detail_info"]["play_second"]) + 1))
            cum_time += (int(text_setting[4]["detail_info"]["play_second"]) + 1)

        info = {}
        info["time"] = {}
        info["time"]["year"] = now_kst.strftime("%Y").zfill(4)
        info["time"]["month"] = now_kst.strftime("%m").zfill(2)
        info["time"]["day"] = now_kst.strftime("%d").zfill(2)
        info["time"]["hour"] = now_kst.strftime("%H").zfill(2)
        info["time"]["minute"] = now_kst.strftime("%M").zfill(2)
        info["time"]["second"] = now_kst.strftime("%S").zfill(2)
        info["time"]["alltime"] = now_kst.strftime("%Y").zfill(4) + now_kst.strftime("%m").zfill(2) + now_kst.strftime(
            "%d").zfill(2) + now_kst.strftime("%H").zfill(2) + now_kst.strftime("%M").zfill(2) + now_kst.strftime(
            "%S").zfill(2)
        sort_time.append(int(info["time"]["alltime"]))

        info["type"] = "string"
        info["action"] = "stop"


    data.append(info)
    # 추가) 기존의 타임테이블 가져와서 시간 중복 처리########################################

    # 최신 타임테이블을 가져옴
    #timetable_list = timetable_list_in_bucket()
    #DOWNLOAD("ynumcl-act", user_id + "/JSON/TIMETABLE/" + timetable_list[-1] ,  user_id+ "/timetable")
    #list_json = read_timetable() # 최근 타임테이블
    #if list_json is None:
    #    list_json = []

    #print(list_json[0]['time']['alltime'])
    sort_time.sort() # 이미지 + 텍스트 => 시작 시간, 끝나는 시간
    #print(list_json)
    #for i in range(0, len(list_json), 2):
        #if (int(list_json[i]['time']["alltime"]) <= sort_time[0]): # 끼어들어야 하는 경우
            #if (int(list_json[i+1]['time']["alltime"]) > sort_time[-1]): # 그사이에 끝나는 경우
                #list_json[i+1]['time']["alltime"] = str(sort_time[-1])
            #else: # 다음거 침범
                #list_json[i+2]['time']["alltime"] = str(sort_time[-1] + 5)
        #else:
            #pass

    #list_json.extend(data)

    ################################################################################

    save_file(data)
    UPLOAD("ynumcl-act", user_id + "/send",
           user_id + "/JSON/TIMETABLE/" + now_kst1.strftime("%Y%m%d%H%M%S"))

    return render(request, 'image.html')

# 사진 GCP에서 다운해서 폴더 home/static에 저장 하는 코드
@csrf_exempt
def save_img(request):
    print("이미지 저장 호출 성공")
    img_list = img_list_in_bucket(user_id)

    change = str(request.body)
    change = int(change[11]) #이건 리스트에서 사진의 인덱스를 저장함
    print(img_list[change])

    DOWNLOAD("ynumcl-act", user_id + "/IMAGE/{}".format(img_list[change]), "home//static//{}.jpg".format(change))
    # 사진 저장도 인덱스.jpg ex) 0.jpg 1.jpg 형식으로 저장함

    return redirect('image.html')



@csrf_exempt
def delete_img(request):
    if request.method == 'POST':
        if request.is_ajax():
            delete_index = int(request.POST['index'])
            delete_index += 1 # 다인이 작성한 인덱스 반환이 -1부터 시작하여 1을 더함
            img_list = img_list_in_bucket("")
            if (delete_index >= len(img_list)):
                pass
            else:
                delete_name = img_list[delete_index]  # 삭제할 파일 이름 (고유번호 포함)
                delete_blob("ynumcl-act", user_id + "/IMAGE/" + delete_name)

            return redirect('image.html')
        else:
            print("ajax 통신 실패!")
            return redirect('image.html')
    else:
        print("POST 호출 실패!")
        return redirect('image.html')


    return redirect('image.html')



@csrf_exempt
def delete_text(request):
    if request.method == 'POST':
        if request.is_ajax():
            delete_index = int(request.POST['index'])
            delete_index += 1 # 다인이 작성한 인덱스 반환이 -1부터 시작하여 1을 더함
            text_list = text_list_in_bucket("")
            if (delete_index >= len(text_list)):
                pass
            else:
                delete_name = text_list[delete_index]  # 삭제할 파일 이름 (고유번호 포함)
                delete_blob("ynumcl-act", user_id + "/JSON/TEXT_LIST/" + delete_name)

            return redirect('image.html')
        else:
            print("ajax 통신 실패!")
            return redirect('image.html')
    else:
        print("POST 호출 실패!")
        return redirect('image.html')


    return redirect('image.html')


#-------------------- for text preview -------------------
@csrf_exempt
def make_text_preview(request):    # 이벤트 전송 버튼 TEXT_LIST에서 선택된 TIMETABLE을 JSON/TIMETABLE로 전송
   print("--------------------> make_text_preview is called <--------------------")

   change = request_body_list_text(request.body)

   text_content = str(change[0])
   axis_x = int(change[1])
   axis_y = int(change[2])
   axis_w = int(change[3])
   axis_h = int(change[4])
   play_speed = int(change[5])
   play_count = int(change[6])
   font_size = int(change[7])
   scroll_fix = str(change[10])
   play_second = int(change[11])
   hex = str("#" + change[8])
   rgb_value = ImageColor.getcolor(hex, "RGB")
   rgb = str(rgb_value)

   print("--------------------> make_text_preview : parameter list and value <--------------------")
   print("text content: " + text_content)
   print("axis x: " + str(axis_x))
   print("axis y: " + str(axis_y))
   print("axis w: " + str(axis_w))
   print("axis h: " + str(axis_h))
   print("play speed: " + str(play_speed))
   print("play count: " + str(play_count))
   print("font size: " + str(font_size))
   print("scroll fixed: " + scroll_fix)
   print("font color: " + rgb)

   if axis_x < 0:
      axis_x = 0
   if axis_y < 0:
      axis_y = 0
   if axis_w < 1:
      axis_w = 1
   if axis_h < 1:
      axis_h = 1
   if not text_content:
      text_content = "ActVision"

   font = "NanumGothic"
   thickness_italics = 0
   background_color = (255, 255, 255)
   text_color = rgb_value

   if os.path.exists("home/static/text_preview.jpg"):
      os.remove("home/static/text_preview.jpg")

   if(font == "NotoSansCJK-Regular.ttc"):
      font = ImageFont.truetype("/usr/share/fonts/opentype/noto/" + font, int(font_size))

   elif(font == "FreeSerif"):
      if(thickness_italics == 0):
         font = ImageFont.truetype("/home/pi/EV/FONTS/FreeSerif/FreeSerif.ttf", int(font_size))
      elif(thickness_italics == 1):
         font = ImageFont.truetype("/home/pi/EV/FONTS/FreeSerif/FreeSerifBold.ttf", int(font_size))
      elif(thickness_italics == 2):
         font = ImageFont.truetype("/home/pi/EV/FONTS/FreeSerif/FreeSerifItalic.ttf", int(font_size))
         # elif(thickness_italics == 3):
         #     font = ImageFont.truetype("/home/pi/EV/FONTS/FreeSerif/FreeSerifBoldItalic.ttf", int(font_size))
   elif(font == "NanumGothic"):
      if(thickness_italics == 0):
         font = ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothic.ttf", int(font_size))
      else: #if(thickness_italics == 1):
         font = ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf", int(font_size))

   im = Image.new('RGB', (axis_w, axis_h), background_color)
   drawer = ImageDraw.Draw(im)
   drawer.text((axis_x, axis_y), text_content, font=font, fill=text_color)

   if axis_w <= 1 or axis_h <= 1:
   # text_height = font_size
      (text_width, text_height) = drawer.textsize(text=text_content, font=font)
      print("--------------------> text width is {}".format(text_width))
      print("--------------------> text height is {}".format(text_height))
      im = Image.new('RGB', (text_width, text_height), background_color)
      drawer = ImageDraw.Draw(im)
      drawer.text((axis_x, axis_y), text_content, font=font, fill=text_color)

   im.save("home/static/text_preview.jpg")
   print("preview image is saved....")

   return redirect('image.html')

