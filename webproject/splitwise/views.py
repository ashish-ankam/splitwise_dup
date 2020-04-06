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

def getNamesOfFriends(user_name): # eturns names of friends of a user
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

def getAmount(user,friend=None):
    cursor=connection.cursor()
    i_spent=None
    others_spent=None
    give=None
    receive=None
    #fetching based on provided username and friend name
    if friend is None:
        cursor.execute("select SUM(amount) from amount_messages where sender=%s",[user])
        i_spent=cursor.fetchall()
        cursor.execute("select SUM(amount) from amount_messages where receiver=%s",[user])
        others_spent=cursor.fetchall()
    else:
        cursor.execute("select SUM(amount) from amount_messages where sender=%s AND receiver=%s",[user,friend])
        i_spent=cursor.fetchall()
        cursor.execute("select SUM(amount) from amount_messages where sender=%s AND receiver=%s",[friend,user])
        others_spent=cursor.fetchall()

    i_spent=i_spent[0][0]
    others_spent=others_spent[0][0]
    #calculationg amount to be given or to be received
    if i_spent is not None and others_spent is not None:
        if(i_spent<others_spent):
            give=others_spent-i_spent
        else:
            receive=i_spent-others_spent
    elif i_spent is not None:
        receive=i_spent
    elif others_spent is not None:
        give=others_spent

    return give,receive

def home(request):
    names_of_friends=getNamesOfFriends(str(request.user))
    cursor = connection.cursor()
    cursor.execute("select SUM(amount) from amount_messages where sender=%s",[str(request.user)])
    i_spent=cursor.fetchall()
    cursor.execute("select SUM(amount) from amount_messages where receiver=%s",[str(request.user)])
    others_spent=cursor.fetchall()
    i_spent=i_spent[0][0]
    others_spent=others_spent[0][0]
    print(i_spent,others_spent)
    if(i_spent-others_spent<0):
        give=others_spent-i_spent
        receive=None
    else:
        give=None
        receive=i_spent-others_spent
    return render(request,'home.html',{'user':str(request.user),'friends':names_of_friends,'chat':None,'give':give,'receive':receive})

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
    friend=request.POST['temp_text']
    msg=request.POST['msg']
    amnt=request.POST['amnt']
    if(amnt==""):
        amnt=0
    cursor=connection.cursor()
    cursor.execute("insert into amount_messages values(%s,%s,%s,%s)",[str(request.user),friend,amnt,msg])
    return redirect(loadChat,friend=friend)

def loadChat(request,friend=None):
    if request.method=='POST':
        friend=request.POST['temp_text']
    cursor=connection.cursor()
    cursor.execute("select * from amount_messages where (sender = %s AND receiver= %s) OR (sender = %s AND receiver= %s)",[str(request.user),friend,friend,str(request.user)])
    msges_with_names=cursor.fetchall()
    names_of_friends=getNamesOfFriends(str(request.user))
    give,receive=getAmount(str(request.user))
    give_to_friend,receive_from_friend=getAmount(str(request.user),friend)
    return render(request,'home.html',{'user':str(request.user),'friend':friend,'give':give,'receive':receive,'give_to_friend':give_to_friend,'receive_from_friend':receive_from_friend,'friends':names_of_friends,'chat':1,'messages':msges_with_names})