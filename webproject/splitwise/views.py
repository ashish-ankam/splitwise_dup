from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User,auth
from django.db.models import Q, Model
from django.db import connection, models
# Create your views here.

from django.template.defaulttags import register

@register.filter
def get_range(value):
    return range(value)
@register.filter
def get_len(value):
    return len(value)

def getNamesOfFriends(user_name):
    cursor = connection.cursor()
    cursor.execute("select * from user_to_user_mapping")
    all_users=cursor.fetchall()
    result=[]
    length=len(user_name)
    for user in all_users:
        string_of_user=user[0]
        if string_of_user[0:length] == user_name and string_of_user[length]== '_':
            result.append(string_of_user[length+1:100])
        else:
            lengt=len(string_of_user)
            i=0
            while i in range(lengt):
                if string_of_user[i] == '_':
                    break
                i+=1
            if string_of_user[i+1:100] == user_name:
                result.append(string_of_user[0:i])
    return result

def home(request):
    names_of_friends=getNamesOfFriends(str(request.user))
    return render(request,'home.html',{'user':request,'friends':names_of_friends})

def login(request):
    if request.method=='POST':
        name=request.POST['name']
        password=request.POST['password']
        user=auth.authenticate(username=name,password=password)
        if user is not None:
            auth.login(request,user)
            return redirect(home)
        else:
            messages.info(request,'email/password error')
            return redirect(login)
    else:       
        return render(request,'login.html')

def signup(request):
    if request.method=='POST':
        name=request.POST['name']
        password1=request.POST['password']
        email=request.POST['email']
        password2=request.POST['re_password']
        if name=="" or password1=="" or password2=="" or email=="":
            messages.info(request,"please fill up all the fields")
            return redirect('signup')
        elif User.objects.filter(username=name).exists():
            messages.info(request,"user name taken")
            return redirect('signup')
        elif password1!=password2:
            messages.info(request,"password error")
            return redirect('signup')
        elif User.objects.filter(email=email).exists():
            messages.info(request,"email taken")
            return redirect('signup')
        else:
            user=User.objects.create_user(username=name,password=password1,email=email)
            user.save()
            auth.login(request,user)
            return redirect(home)
    return render(request,'signup.html')

def addUser(request):
    if request.method=='POST':
        name=request.POST['user']
        users=User.objects.filter(Q(username__icontains=name))
        return render(request,'add_user.html',{'users':users})
    users=User.objects.all()    
    return render(request,'add_user.html',{'users':users})

def addToDb(request):
    friend_name=request.POST['user']
    name=request.user
    cursor = connection.cursor()
    temp_input=friend_name+"_"+str(name)
    cursor.execute("select * from user_to_user_mapping where user_to_user=%s",[temp_input])
    result=cursor.fetchall()
    if len(result) == 0:
        temp_input=str(name)+"_"+friend_name
        cursor.execute("select * from user_to_user_mapping where user_to_user=%s",[temp_input])
        result=cursor.fetchall()
        if len(result) == 0:
            cursor.execute("insert into user_to_user_mapping values(%s)",[temp_input])
    return redirect(home)

def saveMsgToDb(request):
    msg=request.POST['msg']
    cursor=connection.cursor()
    cursor.execute("insert into msges values(%s,%s,%s)",[str(request.user),'sritej',msg])
    return redirect(home)

def loadChat(request):
    friend=request.POST['temp_text']
    cursor=connection.cursor()
    cursor.execute("select msge from msges where sender = %s AND receiver= %s",[str(request.user),friend])
    my_msges=cursor.fetchall()
    cursor.execute("select msge from msges where sender = %s AND receiver= %s",[friend,str(request.user)])
    friend_msges=cursor.fetchall()
    names_of_friends= getNamesOfFriends(str(request.user))
    my_msges= [my_msges[i][0] for i in range(len(my_msges))] 
    friend_msges= [friend_msges[i][0] for i in range(len(friend_msges))]
    print(my_msges)
    print(friend_msges)
    if len(my_msges)> len(friend_msges):    
        length=len(my_msges)
    else:
         length=len(friend_msges)
    return render(request,'home.html',{'user':request,'friends':names_of_friends,'my_msges':my_msges,'friend_msges':friend_msges,'length':length})