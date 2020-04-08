from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User,auth
from django.db.models import Q, Model
from django.db import connection, models
# Create your views here.

def getNamesOfFriends(user_name): # returns names of friends of a user
    cursor = connection.cursor()
    cursor.execute("select * from user_to_user_mapping")
    all_users=cursor.fetchall()
    result=[]
    for user in all_users:
        string_of_user=user[0]
        names_as_list=string_of_user.split('_')
        if user_name in names_as_list:
            if names_as_list[0]==user_name:
                result.append(names_as_list[1])
            else:
                result.append(names_as_list[0])
    return result

def getUsersInGroupAsList(string_of_names):
    return string_of_names.split('_')

def getAllGroups():
    cursor=connection.cursor()
    cursor.execute("select group_name from users_to_group_mapping")
    grp_names=cursor.fetchall()
    return [result[0] for result in grp_names]

def getNamesOfGroupsOfUser(user_name): # returns names of groups of a user
    cursor = connection.cursor()
    cursor.execute("select * from users_to_group_mapping")
    data_from_db=cursor.fetchall()
    result=[]
    for row in data_from_db:
        list_of_names=getUsersInGroupAsList(row[1])
        if user_name in list_of_names:
            result.append(row[0])
    return result

def calculateAmnt(i_spent,others_spent):
    #calculationg amount to be given or to be received
    give=None
    receive=None
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

def getAmount(user,friend=None):
    cursor=connection.cursor()
    i_spent=None
    others_spent=None
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
    
    return calculateAmnt(i_spent,others_spent)

def getAmountForGroup(user,group_name):
    cursor=connection.cursor()
    i_spent=None
    others_spent=None
    cursor.execute("select SUM(amount) from amount_messages where sender =%s AND receiver=%s",[user,group_name])
    i_spent = cursor.fetchall()
    i_spent=i_spent[0][0]
    cursor.execute("select SUM(amount) from amount_messages where sender != %s AND receiver=%s",[user,group_name])
    others_spent=cursor.fetchall()
    others_spent=others_spent[0][0]
    return calculateAmnt(i_spent,others_spent)

def calculateFinalTotalGiveReceives(gives_from_users,receives_from_users,gives_from_groups,receives_from_groups):
    if gives_from_users is None and gives_from_groups is None and receives_from_users is None and receives_from_groups is None:
        return None,None
    if gives_from_users is None and receives_from_users is None:
        return gives_from_groups,receives_from_groups
    if gives_from_groups is None and receives_from_groups is None:
        return gives_from_users,receives_from_users
    if gives_from_users is None and gives_from_groups is None:
        return None,receives_from_users+receives_from_groups
    if receives_from_users is None and receives_from_groups is None:
        return gives_from_users+gives_from_groups,None
    if gives_from_users is None and receives_from_groups is None:
        return calculateAmnt(receives_from_users,gives_from_groups)
    return calculateAmnt(gives_from_users,receives_from_groups)

def calculateOverallGiveReceives(request):
    cursor=connection.cursor()
    #for all groups calculations
    i_spent_for_groups=None
    others_spent_for_groups=None
    give_to_groups = None
    receive_from_groups = None
    groups = getNamesOfGroupsOfUser(str(request.user))
    if groups != []:
        string_to_execute = "select SUM(amount) from amount_messages where sender != '"+str(request.user)+"' AND ("
        for group in groups:
            string_to_execute+="receiver = '"+group+"' OR "
        string_to_execute=string_to_execute[0:len(string_to_execute)-3]+")"
        cursor.execute(string_to_execute)
        others_spent_for_groups = cursor.fetchall()
        others_spent_for_groups=others_spent_for_groups[0][0]
        give_to_groups,receive_from_groups=calculateAmnt(i_spent_for_groups,others_spent_for_groups)

    #for all users calculations
    give,receive = getAmount(str(request.user))
    return calculateFinalTotalGiveReceives(give,receive,give_to_groups,receive_from_groups)
    
def calculateSingleUsersGivesReceives(request,friend):
    groups=getAllGroups()

    if friend in groups:
        give_to_a_chat,receive_from_a_chat = getAmountForGroup(str(request.user),friend)
    else:
        give_to_a_chat,receive_from_a_chat = getAmount(str(request.user),friend)

    return give_to_a_chat,receive_from_a_chat

def getMessagesWithAUser(user,friend):
    groups=getAllGroups()
    cursor=connection.cursor()

    if friend in groups:
        cursor.execute("select * from amount_messages where receiver=%s",[friend])
    else :
        cursor.execute("select * from amount_messages where (sender=%s AND receiver=%s) OR (sender=%s AND receiver=%s)",[user,friend,friend,user])

    return cursor.fetchall()

def loadChat(request,friend=None):
    if request.method=='POST':
        friend=request.POST['temp_text']
    #single chats gives,receives
    give_to_a_chat, receive_from_a_chat = calculateSingleUsersGivesReceives(request,friend)
    #overall gives and receives
    give,receive=calculateOverallGiveReceives(request)
    msges_with_names=getMessagesWithAUser(str(request.user),friend)
    names_of_friends = getNamesOfFriends(str(request.user))
    names_of_groups = getNamesOfGroupsOfUser(str(request.user))
    return render(request,'home.html',{'user':str(request.user),'friend':friend,'give':give,'receive':receive,'give_to_friend':give_to_a_chat,'receive_from_friend':receive_from_a_chat,'friends':names_of_friends,'groups':names_of_groups,'chat':1,'messages':msges_with_names})

def home(request):
    names_of_friends = getNamesOfFriends(str(request.user))
    names_of_groups = getNamesOfGroupsOfUser(str(request.user))
    give,receive = calculateOverallGiveReceives(request)
    return render(request,'home.html',{'user':str(request.user),'friends':names_of_friends,'groups':names_of_groups,'chat':None,'give':give,'receive':receive})

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

def getUsersForUser(request):
    users=User.objects.all()    
    return render(request,'add_user.html',{'users':users})

def addUserToDb(request):
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

def getUsersForGroup(request):
    users=User.objects.all()    
    return render(request,'add_group.html',{'users':users})

def addGroupToDb(request):
    group_name=request.POST['myInput']
    user=str(request.user)
    group_members=request.POST['group_mem']
    group_members=group_members+user
    cursor=connection.cursor()
    cursor.execute("insert into users_to_group_mapping values(%s,%s)",[group_name,group_members])
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

