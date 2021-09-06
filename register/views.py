from logging import root
from django.shortcuts import render, redirect
import os, json
from google.cloud import storage
from google.cloud.storage import blob, bucket
from settings.update_json import *
import datetime
from django.contrib.auth.models import User


# Create your views here.

def register(request):
    get_root_json_from_GCP()
    read_root_json()
    userinfo = User.objects.get(username=request.user.username)
    id_info, pw_info, setup_place, setup_date, company_name, display, max_brgt, serial_number, root_info = show_root_json()
    return render(request, 'register.html',
                  {'userinfo': userinfo, 'id_info': id_info, 'pw_info': pw_info, 'setup_place': setup_place,
                   'setup_date': setup_date, 'company_name': company_name, 'display': display, 'max_brgt': max_brgt,
                   'serial_number': serial_number, 'root_info': root_info})


def users_list(request):  # 조회 버튼을 누르면 사용자 정보들을 불러옴 (사용자 = GCP 버켓 이름)
    return redirect(request, 'register.html')


def get_root_json_from_GCP(bucket_name="ynumcl-act"):  # download the json
    # always raspi serial is 16 string
    os.system("rm -rf " + top_directory + "root/*")  # initailizing the root file,
    blobs = storage_client.list_blobs(bucket_name)
    for i in blobs:
        if (i.name[17:21] == "root"):
            DOWNLOAD(bucket_name, i.name,
                     top_directory + root_directory + i.name[0:16] + "_root.json")  # download with serial + root.json


def read_root_json():
    json_all_list = os.listdir(top_directory + root_directory)
    json_list = []
    for i in range(len(json_all_list)):
        if (len(json_all_list[i]) > 21):
            json_list.append(json_all_list[i])

    json_info = []
    for i in range(len(json_list)):
        json_list[i] = root_directory + json_list[i]
        with open(json_list[i], 'r', encoding="utf-8-sig") as outfile:
            read_json_info = json.load(outfile)
            json_info.append(read_json_info)
    with open(top_directory + root_directory + "all_player.json", 'w', encoding="utf-8-sig") as inputfile:
        json.dump(json_info, inputfile, indent=4, ensure_ascii=False)  # not broken korean, ensure..


def show_root_json():
    with open(top_directory + root_directory + "all_player.json", 'r', encoding='utf-8-sig') as info:
        root_info = json.load(info)
        id_info = [];
        pw_info = [];
        setup_place = [];
        setup_date = [];
        company_name = [];
        display = [];
        max_brgt = [];
        serial_number = [];
        for i in range(len(root_info)):
            id_info.append(root_info[i][2])
            pw_info.append(root_info[i]["pw"])
            setup_place.append(root_info[i]["setup_place"])
            year = int(root_info[i]["setup_day"]["year"]);
            month = int(root_info[i]["setup_day"]["month"]);
            day = int(root_info[i]["setup_day"]["day"]);
            hour = int(root_info[i]["setup_day"]["hour"]);
            minute = int(root_info[i]["setup_day"]["minute"]);
            second = int(root_info[i]["setup_day"]["second"]);
            setup_date.append(datetime.datetime(year, month, day, hour, minute, second).strftime('%Y/%m/%d %H:%M:%S'))
            company_name.append(root_info[i]["company_name"]);
            display.append(root_info[i]["display"]["width"] + 'x' + root_info[i]["display"]["height"]);
            max_brgt.append(int(root_info[i]["max_brightness"]));
            serial_number.append(root_info[i]["serial"]);
            # day3 = datetime.datetime(2020, 12, 14, 14, 10, 50).strftime('%Y-%m-%d %H:%M:%S')

        return id_info, pw_info, setup_place, setup_date, company_name, display, max_brgt, serial_number, root_info