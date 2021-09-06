from django.shortcuts import render
from django.contrib.auth.models import User
# Create your views here.
def inform(request):
    userinfo = User.objects.get(username=request.user.username)
    return render(request,'inform.html',{'userinfo':userinfo})