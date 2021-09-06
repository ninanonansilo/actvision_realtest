from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from settings.update_json import *
from imgn.media_json import *
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from movie.schedule import *
from django.contrib.auth.models import User

# Create your views here.

check_index = -1

def movie(request):
    play_list = directory_list() # 재생목록 이름 리스트 (고유번호 포함)
    list_name = []
    list_date = []
    list_schedule = []
    list_overlap = 0
    print(play_list)
    for i in range(len(play_list)):
        list_date.append(play_list[i][0:4] + '-' + play_list[i][4:6] + '-' + play_list[i][6:8] + ' (' + play_list[i][8:10] +':' +
                         play_list[i][10:12] +')') # 앞에 14자리 - 등록일
        list_name.append(play_list[i][14:])

    print("현재 등록된 재생목록->")
    print(list_name)

    global check_index
    list_index = int(check_index)
    media_list = []
    if (list_index != -1): # 체크된 상태라면 -> 해당 재생목록의 동영상들을 가져오기
        if list_index >= len(play_list):
            pass
        else:
            param_play_list_name = play_list[list_index] # 선택한 재생목록 이름 (고유번호 포함)
            media_list = video_list_in_bucket(param_play_list_name) # 고유번호 14자리를 제외한 동영상 이름
            schedule_list = schedule_list_in_bucket(param_play_list_name, -2) # 재생일정 리스트 (각 , 38자리 / 초기는 14자리)
            list_overlap = check_overlap(schedule_list_in_bucket(param_play_list_name, -2))


            # 쪼개서 UI에 표시할 문자열로 저장 (append) , 14자리(일정 미설정) => 조건 처리하여 '미설정' 표시
            for i in range(len(schedule_list)):
                if (len(schedule_list[i]) == 14): #  재생일정 미등록
                    list_schedule.append("미등록")
                else:
                    list_schedule.append("(" + schedule_list[i][16:18] + "." + schedule_list[i][18:20] + "." + schedule_list[i][20:22] + "~" +
                                         schedule_list[i][24:26] + "." + schedule_list[i][26:28] + "." +schedule_list[i][28:30] + ")"
                                         + schedule_list[i][30:32] + ":" + schedule_list[i][32:34] + "~" + schedule_list[i][34:36] + ":" + schedule_list[i][36:38])


    list_dict = {
        'list_name': list_name,  # 재생목록 -> 이름
        'list_date': list_date,  # 재생목록 -> 등록일
        'list_index': list_index,  # 체크 -> 인덱스
        'list_media': media_list,  # 선택된 재생목록 내 동영상
        'list_schedule' : list_schedule, # 재생일정 표시
        'list_overlap' : list_overlap, #시간중복확인
        }

    print("재생목록 내 동영상 리스트->")
    print(media_list)

    context = json.dumps(list_dict)
    userinfo = User.objects.get(username=request.user.username)
    return render(request, 'mov.html', {'context': context, 'userinfo':userinfo})


@csrf_exempt
def video_list(request):
    temp = request.POST['index']
    global check_index
    check_index = temp

    return render(request, 'mov.html')
    #return redirect('movie.html')




@csrf_exempt
def upload_list(request):  # 재생목록 추가 ( GCP에 해당하는 이름의 디렉토리를 만듬)
    if request.method == 'POST':
        if request.is_ajax():
            print(request.POST['list'])    # 리스트 이름
            input = request.POST['list']
            list_name = input # 임시방편
            # -- 업로드 , 이런식으로 하면 오류 없이 디렉토리 생성가능
            now_kst = time_now()  # 현재시간 받아옴
            UPLOAD("ynumcl-act", 'test' , user_id + "/PLAY_LIST/" + now_kst.strftime("%Y%m%d%H%M%S") + str(list_name) + "/")
            return redirect('movie.html')
        else:
            print("ajax 통신 실패!")
            return redirect('movie.html')
    else:
        print("POST 호출 실패!")
        return redirect('movie.html')



def directory_list():   # 디렉토리가 '/'로 끝나는 특징을 사용해 디렉토리 이름만 추출
    play_list_name = play_list_in_bucket("ynumcl-act")  # 중복 확인을 위해 PLAY_LIST 하위 이름들의 배열
    list_name = []
    for i in range(len(play_list_name)):
        if play_list_name[i][-1:] == '/':
            list_name.append(play_list_name[i][:-1])
    return list_name


@csrf_exempt
def upload_video(request):  # 재생목록에 동영상 업로드
    if request.method == 'POST':
        if request.is_ajax():

            video_name = request.POST['video_name']  # 동영상 이름
            play_list_index = int(request.POST['list_name']) # 재생목록 인덱스
            if (play_list_index == -1):  # 재생목록이 선택되지 않은 상태라면 저장하지 않음
                return redirect('movie.html')
            video = request.FILES.get('video')  # 동영상을 request에서 받아옴
            path = default_storage.save(user_id + "/video", ContentFile(video.read()))
            play_list = directory_list()
            checked_play_list = play_list[play_list_index]
            now_kst = time_now()  # 현재시간 받아옴
# 찬호야 부탁해

            UPLOAD("ynumcl-act", user_id + "/video",user_id + "/PLAY_LIST/" + checked_play_list + now_kst.strftime("/%Y%m%d%H%M%S") + video_name)
            UPLOAD("ynumcl-act", "test" ,user_id + "/VIDEO_SCHEDULE/" + checked_play_list + now_kst.strftime("/%Y%m%d%H%M%S"))

            os.remove(user_id + "/video")  # 장고에서 중복된 이름의 파일에는 임의로 이름을 변경하기 때문에 임시파일은 제거
            return redirect('movie.html')
        else:
            print("ajax 통신 실패!")
            return redirect('movie.html')
    else:
        print("POST 호출 실패!")
        return redirect('movie.html')


@csrf_exempt
def delete_play_list(request):  # 선택된 재생목록 삭제
    if request.method == 'POST':
        if request.is_ajax():

            delete_index = int(request.POST['play_list_index'])
            play_list = directory_list()
            if (delete_index >= len(play_list)):
                pass
            else:
                delete_name = play_list[delete_index]
                delete_blob("ynumcl-act", user_id + "/PLAY_LIST/" + delete_name + "/")

            return redirect('movie.html')
        else:
            print("ajax 통신 실패!")
            return redirect('movie.html')
    else:
        print("POST 호출 실패!")
        return redirect('movie.html')


@csrf_exempt
def delete_video(request):  # 선택된 재생목록 삭제
    if request.method == 'POST':
        if request.is_ajax():
            video_index = int(request.POST['video_index'])
            play_list_index = int(request.POST['play_list_index'])

            play_list = directory_list()
            if (play_list_index >= len(play_list)):
                pass
            else:
                play_list_name = play_list[play_list_index] # 지울 동영상이 속해있는 재생목록 이름 (고유번호 포함)
                video_name_list = video_list_in_bucket_include_code(play_list_name)
                if (video_index >= len(video_name_list)): # 없는 부분의 체크박스 선택시
                    pass
                else:
                    # 동영상 삭제
                    delete_blob("ynumcl-act", user_id + "/PLAY_LIST/" + play_list_name + "/" + video_name_list[video_index])
                    # 스케쥴도 삭제
                    delete_schedule_name = schedule_list_in_bucket(play_list_name, video_index)
                    delete_blob("ynumcl-act", user_id + "/VIDEO_SCHEDULE/" + play_list_name + "/" + delete_schedule_name)

            return redirect('movie.html')
        else:
            print("ajax 통신 실패!")
            return redirect('movie.html')
    else:
        print("POST 호출 실패!")
        return redirect('movie.html')



@csrf_exempt
def play_schedule(request):
    if request.method == 'POST':
        if request.is_ajax():

            start_day = request.POST["start_day"]
            start_day = re.sub(r'[^0-9]', '', start_day)
            finish_day = request.POST["finish_day"]
            finish_day = re.sub(r'[^0-9]', '', finish_day)
            start_hour = request.POST["start_hour"]
            finish_hour = request.POST["finish_hour"]
            start_min = request.POST["start_min"]
            finish_min = request.POST["finish_min"]
            video_index = int(request.POST["video_index"])
            play_list_index = request.POST["play_list_index"]
            print(start_day , finish_day)
            # 선택한 인덱스의 파일이름을 가져와 14자리 떼어냄
            play_list = directory_list()
            play_list_name = play_list[int(play_list_index)] # 재생목록 이름 (14자리 포함)
            video_list = video_list_in_bucket_only_code(play_list_name) # 현재 보고있는 동영상 리스트
            file_code = video_list[video_index]  # file_code => 고유번호 14자리

            if (video_index >= len(video_list)):
                pass
            else:
                # VIDEO_SCH EDULE -> 선택 파일의 현재 이름
                rename_prev = schedule_list_in_bucket(play_list_name ,video_index)

                new_name = str(file_code) + start_day + finish_day + start_hour + start_min + finish_hour + finish_min
                # VIDEO_SCHEDULE에 등록한 스케쥴로 변경
                rename_blob("ynumcl-act" , user_id + "/VIDEO_SCHEDULE/" + play_list_name + "/" + rename_prev
                            ,user_id + "/VIDEO_SCHEDULE/" + play_list_name + "/" + new_name)



            return redirect('movie.html')
        else:
            print("ajax 통신 실패!")
            return redirect('movie.html')
    else:
        print("POST 호출 실패!")
        return redirect('movie.html')

@csrf_exempt
def check_overlap(input):
    length = len(input)
    clear_input = []

    for i in range(length):
        if (len(input[i]) == 38):
            input[i] = input[i][14:]
            print(input[i])
            clear_input.append(input[i])
    clear_input.sort()
    clear_input
    input = clear_input
    input
    length = len(input)
    for j in range(length - 1):
        temp = input[j]
        for i in range(j, length - 1):
            if (input[i + 1][0:7]) < temp[8:16]:
                if (input[i + 1][16:20]) < temp[20:23]:
                    return True
                else:
                    return False
            else:
                return False

@csrf_exempt
def play_list_trans(request): # 재생목록 전송
    if request.method == 'POST':
        if request.is_ajax():
            play_list_index = int(request.POST["index"])
            now_kst = time_now()
            # 인덱스로 재생목록 이름 따 옴
            play_list = directory_list()
            play_list_name = play_list[play_list_index]

            # 따온 재생목록 이름으로 동영상 스케쥴 폴더 -> 재생목록 이름 으로 접근
            schedule_list = schedule_list_in_bucket(play_list_name, -2)


            data = []
            # 해당 디렉토리의 이름들로 스케쥴 작성 , 일정 미작성 동영상(또는 과거) 모두 고려
            for i in range(len(schedule_list)): # 스케쥴 개수(재생목록 내 동영상 개수) 만큼 반복
                print(schedule_list)
                if len(schedule_list[i]) <= 14:  # 최초 등록 후 일정추가를 안한 영상은 패스
                    pass
                elif len(schedule_list[i]) == 38: # 한개의 동영상
                    # 해당 동영상 PLAY_LIST -> MEDIA/video로 옮기는 작업
                    video_name_list = video_list_in_bucket_include_code(play_list_name) # 동영상(풀 네임) 리스트
                    print("ghkrdls")
                    print(play_list_name)
                    print(video_name_list)
                    copy_blob("ynumcl-act", user_id + "/PLAY_LIST/" + play_list_name +"/" + video_name_list[i],
                              "ynumcl-act", user_id + "/MEDIA/video/" + video_name_list[i][14:])
                    list_date = diff_date(schedule_list[i][14:22],schedule_list[i][22:30]) # 날짜 리스트 반환 (str)
                    for j in range(len(list_date)):
                        info = {}
                        info["time"] = {}
                        info["time"]["year"] = list_date[j][:4]
                        info["time"]["month"] = list_date[j][4:6]
                        info["time"]["day"] = list_date[j][6:8]
                        info["time"]["hour"] = schedule_list[i][30:32]
                        info["time"]["minute"] = schedule_list[i][32:34]
                        info["time"]["second"] = "10"
                        info["time"]["alltime"] = list_date[j] + schedule_list[i][30:34] + "00"
                        info["type"] = "video"
                        info["action"] = "play"
                        info["title"] = [video_name_list[i][14:]]
                        data.append(info)

                        info = {}
                        info["time"] = {}
                        info["time"]["year"] = list_date[j][:4]
                        info["time"]["month"] = list_date[j][4:6]
                        info["time"]["day"] = list_date[j][6:8]
                        info["time"]["hour"] = schedule_list[i][34:36]
                        info["time"]["minute"] = schedule_list[i][36:38]
                        info["time"]["second"] = "00"
                        info["time"]["alltime"] = list_date[j] + schedule_list[i][34:38] + "00"
                        info["type"] = "video"
                        info["action"] = "stop"

                        data.append(info)
                else:
                    print("스케줄 자릿수 error")
                    pass
            video_names = video_list_in_bucket(play_list_name)
            for i in range(len(video_names)):  # 재생목록안 영상들 모두 업로드
                copy_blob("ynumcl-act", user_id + "/PLAY_LIST/" + play_list_name + "/" + video_name_list[i] , "ynumcl-act",
                      user_id + "/MEDIA/video/" + video_names[i])

            save_file(data)
            UPLOAD("ynumcl-act", user_id + "/send" ,user_id + "/JSON/TIMETABLE/" + now_kst.strftime("%Y%m%d%H%M%S"))
            # 타임테이블을 새로작성하여 기존 타임테이블을 다 죽임
            # 아직 파일 저장만하고 업로드는 넣지않음

            return redirect('movie.html')
        else:
            print("ajax 통신 실패!")
            return redirect('movie.html')
    else:
        print("POST 호출 실패!")
        return redirect('movie.html')



