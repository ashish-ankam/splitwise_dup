from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User, auth
from django.db.models import Q, Model
from django.db import connection, models
from .models import *
from django.core import serializers
# Create your views here.


def roundOffTheResult(give, receive):
    if give is not None:
        give = round(give, 2)
    elif receive is not None:
        receive = round(receive, 2)
    return give, receive


def getUsersInGroupAsList(string_of_names):
    return string_of_names.split('_')


def getNamesOfGroupsOfUser(user_id):  # returns names of groups of a user
    cursor = connection.cursor()
    cursor.execute("select id,group_name from splitwise_group_name_group_id where id in(select group_id from splitwise_users_to_group_mapping where user_id = %s)",[str(user_id)])
    group_names = cursor.fetchall()
    print(group_names)
    return [group_name for group_name in group_names]


def getNoOfMembersInAGroup(group_id):
    cursor = connection.cursor()
    cursor.execute(
        "select count_of_users from splitwise_group_members_count where group_id=%s", [group_id])
    string_of_names = cursor.fetchall()
    return string_of_names[0][0]


def getAllGroups():
    cursor = connection.cursor()
    cursor.execute("select distinct(group_name) from splitwise_users_to_group_mapping")
    grp_names = cursor.fetchall()
    return [result[0] for result in grp_names]


def getNamesOfFriends(user_id):  # returns names of friends of a user
    cursor = connection.cursor()
    cursor.execute("select id,username from auth_user where id in(select user1 from splitwise_user_to_user_mapping where user2 = %s)",[str(user_id)])
    all_users = cursor.fetchall()
    cursor.execute("select id,username from auth_user where id in( select user2 from splitwise_user_to_user_mapping where user1 = %s)",[str(user_id)])
    all_users += cursor.fetchall()
    return [user for user in all_users]


def calculateAmnt(i_spent, others_spent):
    # calculationg amount to be given or to be received
    give = None
    receive = None
    if i_spent is not None and others_spent is not None:
        if(i_spent < others_spent):
            give = others_spent-i_spent
        else:
            receive = i_spent-others_spent
    elif i_spent is not None:
        receive = i_spent
    elif others_spent is not None:
        give = others_spent
    return give, receive


def divideAmount(i_spent, others_spent, group=None):
    if group is None:  # that means it is with a friend
        if i_spent is not None:
            i_spent /= 2
        if others_spent is not None:
            others_spent /= 2
    else:
        no_of_group_members = getNoOfMembersInAGroup(group)
        if i_spent is not None:
            i_spent = ((no_of_group_members-1)*i_spent)/no_of_group_members
        if others_spent is not None:
            others_spent = others_spent/no_of_group_members
    return i_spent, others_spent


def getAmountForSingleUser(user_id, friend_id):
    cursor = connection.cursor()
    i_spent = None
    others_spent = None
    cursor.execute(
        "select SUM(amount) from splitwise_amount_messages_user_to_user where sender=%s AND receiver=%s", [user_id, friend_id])
    i_spent = cursor.fetchall()
    cursor.execute(
        "select SUM(amount) from splitwise_amount_messages_user_to_user where sender=%s AND receiver=%s", [friend_id, user_id])
    others_spent = cursor.fetchall()
    i_spent = i_spent[0][0]
    others_spent = others_spent[0][0]
    # this divides the amount between users
    i_spent, others_spent = divideAmount(i_spent, others_spent)
    # this gives overall thing i.e whether to give or receive money
    return calculateAmnt(i_spent, others_spent)


def getAmountForAllUsers(user):
    cursor = connection.cursor()
    i_spent = None
    others_spent = None
    cursor.execute(
        "select SUM(amount) from splitwise_amount_messages_user_to_user where sender=%s", [user])
    i_spent = cursor.fetchall()
    cursor.execute(
        "select SUM(amount) from splitwise_amount_messages_user_to_user where receiver=%s", [user])
    others_spent = cursor.fetchall()
    i_spent = i_spent[0][0]
    others_spent = others_spent[0][0]
    # this divides the amount between users
    i_spent, others_spent = divideAmount(i_spent, others_spent)
    # this gives overall thing i.e whether to give or receive money
    return calculateAmnt(i_spent, others_spent)


def getAmountForGroup(user_id, group_id):
    cursor = connection.cursor()
    i_spent = None
    others_spent = None
    cursor.execute("select SUM(amount) from splitwise_amount_messages_users_to_group where sender =%s AND group_id=%s", [
                   user_id, group_id])
    i_spent = cursor.fetchall()
    i_spent = i_spent[0][0]
    cursor.execute("select SUM(amount) from splitwise_amount_messages_users_to_group where sender != %s AND group_id=%s", [
                   user_id, group_id])
    others_spent = cursor.fetchall()
    others_spent = others_spent[0][0]
    i_spent, others_spent = divideAmount(i_spent, others_spent, group_id)
    return calculateAmnt(i_spent, others_spent)


def getAmountForAllGroups(request):
    i_spent_for_groups = None
    others_spent_for_groups = None
    temp_i_spent_for_groups = 0
    temp_others_spent_for_groups = 0
    give_to_groups = None
    receive_from_groups = None
    groups = getNamesOfGroupsOfUser(str(request.user))
    if groups != []:
        for group in groups:
            others_spent_for_groups, i_spent_for_groups = getAmountForGroup(
                str(request.user), group)
            if i_spent_for_groups is not None:
                temp_i_spent_for_groups += i_spent_for_groups
            if others_spent_for_groups is not None:
                temp_others_spent_for_groups += others_spent_for_groups
        if temp_i_spent_for_groups != 0:
            i_spent_for_groups = temp_i_spent_for_groups
        if temp_others_spent_for_groups != 0:
            others_spent_for_groups = temp_others_spent_for_groups
        give_to_groups, receive_from_groups = calculateAmnt(
            i_spent_for_groups, others_spent_for_groups)
    return give_to_groups, receive_from_groups


def calculateOverallGiveReceives(request):
    # for all groups calculations
    give_to_groups, receive_from_groups = getAmountForAllGroups(request)
    # for all users calculations
    give, receive = getAmountForAllUsers(str(request.user))
    return calculateFinalOverallGiveReceives(give, receive, give_to_groups, receive_from_groups)


def calculateFinalOverallGiveReceives(gives_from_users, receives_from_users, gives_from_groups, receives_from_groups):
    if gives_from_users is None and gives_from_groups is None and receives_from_users is None and receives_from_groups is None:
        return None, None
    if gives_from_users is None and receives_from_users is None:
        return gives_from_groups, receives_from_groups
    if gives_from_groups is None and receives_from_groups is None:
        return gives_from_users, receives_from_users
    if gives_from_users is None and gives_from_groups is None:
        return None, receives_from_users+receives_from_groups
    if receives_from_users is None and receives_from_groups is None:
        return gives_from_users+gives_from_groups, None
    if gives_from_users is None and receives_from_groups is None:
        return calculateAmnt(receives_from_users, gives_from_groups)
    return calculateAmnt(gives_from_users, receives_from_groups)


def calculateSingleUsersGivesReceives(user_id, friend_id, group):
    #groups = getAllGroups()
    if group=='1':
        give_to_a_chat, receive_from_a_chat = getAmountForGroup(
            user_id, friend_id)
    else:
        give_to_a_chat, receive_from_a_chat = getAmountForSingleUser(
            user_id, friend_id)
    return give_to_a_chat, receive_from_a_chat


def getMessagesWithAUser(user_id, friend_id, group):
    cursor = connection.cursor()
    if group=='1':
        cursor.execute(
            "select t3.username,t2.group_name,t1.amount,t1.message from splitwise_amount_messages_users_to_group t1, splitwise_group_name_group_id t2, auth_user t3 where (t1.group_id=%s and t1.group_id = t2.id) and t1.sender = t3.id", [friend_id])
    else:
        cursor.execute(
            "select sender,receiver,amount,message from splitwise_amount_messages_user_to_user where (sender=%s AND receiver=%s) OR (sender=%s AND receiver=%s)", [user_id, friend_id, friend_id, user_id])
    return cursor.fetchall()


def login(request):
    if request.method == 'POST':
        name = request.POST['email']
        password = request.POST['password']
        cursor = connection.cursor()
        cursor.execute("select username from auth_user where email = %s",[name])
        name = cursor.fetchall()
        if name != []:
            name = name[0][0]
            user = auth.authenticate(username=name, password=password)
            if user is not None:
                auth.login(request, user)
                return redirect(home)
        messages.info(request, 'email/password error')
        return redirect(login)
    else:
        return render(request, 'login.html')


def signup(request):
    if request.method == 'POST':
        name = request.POST['reg_name']
        password1 = request.POST['reg_password']
        email = request.POST['reg_email']
        password2 = request.POST['reg_re_password']
        if name == "" or password1 == "" or password2 == "" or email == "":
            messages.info(request, "please fill up all the fields")
            return redirect('signup')
        elif password1 != password2:
            messages.info(request, "Make sure you enter same password in both the fields")
            return redirect('signup')
        elif User.objects.filter(email=email).exists():
            messages.info(request, "email already in use")
            return redirect('signup')
        else:
            user = User.objects.create_user(
                username=name, password=password1, email=email)
            user.save()
            auth.login(request, user)
            return redirect(home)   
    return render(request, 'login.html')


def home(request):
    cursor = connection.cursor()
    cursor.execute(
        "select id from auth_user where username=%s", [str(request.user)])
    user_id = cursor.fetchall()
    user_id = user_id[0][0]
    names_of_friends = getNamesOfFriends(user_id)
    names_of_groups = getNamesOfGroupsOfUser(user_id)
    #give, receive = calculateOverallGiveReceives(request)
    #give, receive = roundOffTheResult(give, receive)
    return render(request, 'home.html', {'user': str(request.user), 'friends': names_of_friends, 'groups': names_of_groups, 'chat': None, 'user_id': user_id})


def loadChat(request):
    
    friend_id = request.GET['friend_id']
    user_id = request.GET['user_id']
    friend_name = request.GET['friend_name']
    group = request.GET['group']
    # single chats gives,receives
    #give_to_a_chat, receive_from_a_chat = calculateSingleUsersGivesReceives(
        #request, friend)
    # overall gives and receives
    #give, receive = calculateOverallGiveReceives(request)

    #give, receive = roundOffTheResult(give, receive)
    #give_to_a_chat, receive_from_a_chat = roundOffTheResult(
       # give_to_a_chat, receive_from_a_chat)
    #msges_with_names = getMessagesWithAUser(str(request.user), friend)
    #names_of_friends = getNamesOfFriends(str(request.user))
    #names_of_groups = getNamesOfGroupsOfUser(str(request.user))
    #group = None # this is used at client side to recognize whether a chat is with group or not
    #if friend in names_of_groups:
    #    group = 1 # some random values other than None
    return render(request, 'chat.html',{'friend_name':friend_name, 'user_id':user_id,'friend_id':friend_id,'group':group})


def getUsersForAddingUser(request):
    users=[]
    word = request.GET['word']
    user_id = request.GET['user_id']
    if(word!=''):
        users = User.objects.values_list('id','username','email').filter(~Q(id = user_id) & Q(username__icontains = word))
    #users = User.objects.filter(~Q(username = str(request.user)))
    lis = list(users)
    #qs_json = serializers.serialize('json', users)
    from django.http import JsonResponse
    return JsonResponse(lis, safe=False)

def getAddUserTemplate(request):
    user_id = request.GET['user_id']
    return render(request,'add_user.html',{'user_id':user_id})


def addUserToDb(request):
    friend_id = request.GET['friend_id']
    user_id = request.GET['user_id']
    print("HI")
    cursor = connection.cursor()
    cursor.execute(
        "select * from splitwise_user_to_user_mapping where (user1=%s AND user2 = %s) OR (user1=%s AND user2 = %s)", [user_id,friend_id,friend_id,user_id])
    result = cursor.fetchall()
    print(result)
    if len(result) == 0:
        print("HI")
        obj = user_to_user_mapping(user1 = user_id, user2 = friend_id)
        obj.save()
    return redirect(home)


def getAddGrpTemplate(request):
    user_id = request.GET['user_id']
    return render(request,'add_group.html',{'user_id':user_id})


def getUsers(request):
    users=[]
    word = request.GET['word']
    user_id = request.GET['user_id']
    if(word!=''):
        users = User.objects.values_list('id','username','email').filter(~Q(id = user_id) & Q(username__icontains = word))
    #users = User.objects.filter(~Q(username = str(request.user)))
    lis = list(users)
    #qs_json = serializers.serialize('json', users)
    from django.http import JsonResponse
    return JsonResponse(lis, safe=False)


def addGroupToDb(request):
    group_name = request.POST['myInput']
    #user = str(request.user)
    group_ids = request.GET['group_mem']
    user_id = request.GET['user_id']
    group_ids = getUsersInGroupAsList(group_ids+user_id)
    obj = group_name_group_id(group_name = group_name)
    obj.save()
    cursor = connection.cursor()
    cursor.execute(
        "select id from splitwise_group_name_group_id where group_name = %s order by id desc",[group_name])
    group_id = cursor.fetchall()[0][0]
    for user_id in group_ids:
        obj = users_to_group_mapping(group_id = group_id, user_id = user_id)
        obj.save()
    obj = group_members_count(group_id = group_id, count_of_users = len(group_ids))
    obj.save()
    return redirect(home)


def amountForChat(request):
    friend_id = request.GET['friend_id']
    group = request.GET['group']
    user_id = request.GET['user_id']
    # single chats gives,receives
    give_to_a_chat, receive_from_a_chat = calculateSingleUsersGivesReceives(
        user_id, friend_id,group)
    # overall gives and receives
    #give, receive = calculateOverallGiveReceives(request)
    #give, receive = roundOffTheResult(give, receive)
    give_to_a_chat, receive_from_a_chat = roundOffTheResult(
        give_to_a_chat, receive_from_a_chat)
    if receive_from_a_chat is None:
        receive_from_a_chat = 0
    if give_to_a_chat is None:
        give_to_a_chat = 0
    ans = receive_from_a_chat - give_to_a_chat
    print(ans)
    return HttpResponse(str(ans))


def getNewMsges(request):
    friend_id = request.GET['friend_id']
    limit = str(request.GET['limit'])
    group = request.GET['group']
    user_id = request.GET['user_id']
    cursor = connection.cursor()
    if(group=='0'):
        cursor.execute("select L.username,S.amount,S.message,S.sender,S.id from splitwise_amount_messages_user_to_user S, auth_user L where ((S.sender = %s and S.receiver = %s) or (S.sender = %s and S.receiver = %s)) and L.id = S.sender order by S.id desc limit %s",[user_id,friend_id,friend_id,user_id,limit])
    else:
        cursor.execute("select L.group_name,S.amount,S.message,S.sender,S.id from splitwise_amount_messages_users_to_group S, splitwise_group_name_group_id L where S.group_id = %s and L.id = S.group_id order by S.id desc limit %s",[friend_id,limit])
    messages = cursor.fetchall()
    
    from django.http import JsonResponse
    return JsonResponse(list(messages), safe=False)


def getOlderMsges(request):
    friend_id = request.GET['friend_id']
    limit = str(request.GET['limit'])
    offset = str(request.GET['offset'])
    user_id = request.GET['user_id']
    group = request.GET['group']
    cursor = connection.cursor()
    if(group=='0'):
        cursor.execute("select L.username,S.amount,S.message,S.sender,S.id from splitwise_amount_messages_user_to_user S, auth_user L where ((S.sender = %s and S.receiver = %s) or (S.sender = %s and S.receiver = %s)) and L.id = S.sender order by S.id desc limit %s offset %s",[user_id,friend_id,friend_id,user_id,limit,offset])
    else:
        cursor.execute("select L.group_name,S.amount,S.message,S.sender,S.id from splitwise_amount_messages_users_to_group S, splitwise_group_name_group_id L where S.group_id = %s and L.id = S.group_id order by S.id desc limit %s offset %s",[friend_id,limit,offset])
    messages = cursor.fetchall()
    from django.http import JsonResponse
    return JsonResponse(list(messages), safe=False)
    

def saveMsgToDb(request):
    friend_id = request.POST['friend_id']
    user_id = request.POST['user_id']
    group = request.POST['group']
    msg = request.POST['msg']
    amnt = request.POST['amnt']
    if(amnt == ""):
        amnt = 0
    try:
        if group=='1':
            obj = amount_messages_users_to_group(sender = user_id,group_id = friend_id, amount = amnt, message = msg)
            obj.save()
        else:
            obj = amount_messages_user_to_user(sender = user_id,receiver = friend_id, amount = amnt, message = msg)
            obj.save()
        return HttpResponse('true')
    except:
        return HttpResponse('false')


def clearChat(request):
    friend_id = request.GET['friend_id']
    user_id = request.GET['user_id']
    group = request.GET['group']
    cursor = connection.cursor()
    if group=='0':
        cursor.execute("delete from splitwise_user_to_user_mapping where (user1=%s AND user2=%s) OR (user1=%s AND user2=%s)", [
                    user_id, friend_id,friend_id,user_id])
        cursor.execute("delete from splitwise_amount_messages_user_to_user where (sender=%s and receiver=%s) or (sender=%s and receiver=%s)", [
                    friend_id, user_id, user_id, friend_id])
    else:
    # fetch group members then remove user name then update the data in DB
        cursor.execute(
            "select count_of_users from splitwise_group_members_count where group_id=%s", [friend_id])
        count = cursor.fetchall()
        if count !=[]:
            count = count[0][0]
            # remove user share from the group
            cursor.execute("delete from splitwise_amount_messages_users_to_group where sender=%s and group_id=%s", [
                        user_id, friend_id])
            if count == 2:
                cursor.execute(
                    "delete from splitwise_users_to_group_mapping where group_id = %s", [friend_id])
                cursor.execute(
                    "delete from splitwise_amount_messages_users_to_group where group_id =%s", [friend_id])
                cursor.execute(
                    "delete from splitwise_group_members_count where group_id =%s", [friend_id])
                cursor.execute(
                    "delete from splitwise_group_name_group_id where group_id =%s", [friend_id])
            else:
                cursor.execute(
                    "update splitwise_amount_messages_users_to_group set amount = (amount*(%s-1))/%s where group_id = %s", [count, count,friend_id])
                cursor.execute(
                    "delete from splitwise_users_to_group_mapping where user_id = %s AND group_id = %s", [user_id,friend_id])
                cursor.execute(
                    "update splitwise_group_members_count SET count_of_users=count_of_users-1 where group_id = %s", [friend_id])
    return redirect(home)


def divideAmountForGroupGivings(i_spent_for_group, others_spent,group_id):
    no_of_members = getNoOfMembersInAGroup(group_id)
    i_spent_for_each = float(i_spent_for_group/no_of_members)
    givings_for_group = []
    for other_spent in others_spent:
        friend_spent_for_me = float(others_spent[other_spent]/no_of_members)
        if i_spent_for_each - friend_spent_for_me != 0:
            element =[]
            element.append(other_spent)
            element.append(i_spent_for_each - friend_spent_for_me)
            givings_for_group.append(element)
    return givings_for_group


def groupGivings(request):
    friend = request.GET['friend']
    friend_id = request.GET['friend_id']
    user_id = request.GET['user_id']
    group = request.GET['group']
    msges_with_names = getMessagesWithAUser(user_id, friend_id,group)
    i_spent_for_group = 0
    other_mem ={}
    #cursor =connection.cursor()
    #cursor.execute("select user_name from splitwise_users_to_group_mapping where group_id = %s",[friend_id])
    #group_members = cursor.fetchall()
    #group_members = [user[0] for user in group_members]
    #for member in group_members:
     #   if member != str(request.user):
      #      other_mem[member] = 0
    cursor =connection.cursor()
    cursor.execute("select t1.username from splitwise_users_to_group_mapping t2, auth_user t1 where t2.group_id = %s and t1.id = t2.user_id",[friend_id])
    group_idss = cursor.fetchall()
    print(group_idss)
    for user in group_idss:
        if user[0] != str(request.user):
            other_mem[user[0]] = 0
    #calculating every persons expenditure in a group
    for msg in msges_with_names:
        if msg[0] == str(request.user):
            i_spent_for_group += msg[2]
        else:
            other_mem[msg[0]] += msg[2]
    print(other_mem)
    givings_for_group = divideAmountForGroupGivings(i_spent_for_group, other_mem, friend_id)
    print(givings_for_group)
    return render(request,'group_givings.html',{'givings':givings_for_group,'group':friend})