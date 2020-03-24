from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User,auth
from django.db.models import Q
from django.db import connection
# Create your views here.

def getNamesOfFriends(all_users,user_name):
    result=[]
    length=len(user_name)
    for user in all_users:
        string_of_user=user[0]
        if string_of_user[0:length] == user_name and string_of_user[length]== '_':
            result.append(string_of_user[length+1:100])
        elif string_of_user[length+1:100] == user_name and string_of_user[length]== '_':
            result.append(string_of_user[0:length])
    return result

def home(request):
    cursor = connection.cursor()
    cursor.execute("select * from user_to_user_mapping")
    result=cursor.fetchall()
    names_of_friends=getNamesOfFriends(result,str(request.user))
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
            print(request.user)
            return redirect(home)
    return render(request,'signup.html')

def chat(request):
    return render(request,'chat.html')

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
    print(type(result))
    if len(result) is 0:
        temp_input=str(name)+"_"+friend_name
        cursor.execute("select * from user_to_user_mapping where user_to_user=%s",[temp_input])
        result=cursor.fetchall()
        if len(result) is 0:
            cursor.execute("insert into user_to_user_mapping values(%s)",[temp_input])
    return redirect(home)