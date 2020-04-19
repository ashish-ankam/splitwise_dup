from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User, auth
from django.db.models import Q, Model
from django.db import connection, models
# Create your views here.


def roundOffTheResult(give, receive):
    if give is not None:
        give = round(give, 2)
    elif receive is not None:
        receive = round(receive, 2)
    return give, receive


def getUsersInGroupAsList(string_of_names):
    return string_of_names.split('_')


def getNamesOfGroupsOfUser(user_name):  # returns names of groups of a user
    cursor = connection.cursor()
    cursor.execute("select * from users_to_group_mapping")
    data_from_db = cursor.fetchall()
    result = []
    for row in data_from_db:
        list_of_names = getUsersInGroupAsList(row[1])
        if user_name in list_of_names:
            result.append(row[0])
    return result


def getNoOfMembersInAGroup(group):
    cursor = connection.cursor()
    cursor.execute(
        "select count_of_users from users_to_group_mapping where group_name=%s", [group])
    string_of_names = cursor.fetchall()
    return string_of_names[0][0]


def getAllGroups():
    cursor = connection.cursor()
    cursor.execute("select group_name from users_to_group_mapping")
    grp_names = cursor.fetchall()
    return [result[0] for result in grp_names]


def getNamesOfFriends(user_name):  # returns names of friends of a user
    cursor = connection.cursor()
    cursor.execute("select * from user_to_user_mapping")
    all_users = cursor.fetchall()
    result = []
    for user in all_users:
        string_of_user = user[0]
        names_as_list = string_of_user.split('_')
        if user_name in names_as_list:
            if names_as_list[0] == user_name:
                result.append(names_as_list[1])
            else:
                result.append(names_as_list[0])
    return result


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


def getAmountForSingleUser(user, friend):
    cursor = connection.cursor()
    i_spent = None
    others_spent = None
    cursor.execute(
        "select SUM(amount) from amount_messages_user_to_user where sender=%s AND receiver=%s", [user, friend])
    i_spent = cursor.fetchall()
    cursor.execute(
        "select SUM(amount) from amount_messages_user_to_user where sender=%s AND receiver=%s", [friend, user])
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
        "select SUM(amount) from amount_messages_user_to_user where sender=%s", [user])
    i_spent = cursor.fetchall()
    cursor.execute(
        "select SUM(amount) from amount_messages_user_to_user where receiver=%s", [user])
    others_spent = cursor.fetchall()
    i_spent = i_spent[0][0]
    others_spent = others_spent[0][0]
    # this divides the amount between users
    i_spent, others_spent = divideAmount(i_spent, others_spent)
    # this gives overall thing i.e whether to give or receive money
    return calculateAmnt(i_spent, others_spent)


def getAmountForGroup(user, group_name):
    cursor = connection.cursor()
    i_spent = None
    others_spent = None
    cursor.execute("select SUM(amount) from amount_messages_users_to_group where sender =%s AND group_name=%s", [
                   user, group_name])
    i_spent = cursor.fetchall()
    i_spent = i_spent[0][0]
    cursor.execute("select SUM(amount) from amount_messages_users_to_group where sender != %s AND group_name=%s", [
                   user, group_name])
    others_spent = cursor.fetchall()
    others_spent = others_spent[0][0]
    i_spent, others_spent = divideAmount(i_spent, others_spent, group_name)
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


def calculateSingleUsersGivesReceives(request, friend):
    groups = getAllGroups()
    if friend in groups:
        give_to_a_chat, receive_from_a_chat = getAmountForGroup(
            str(request.user), friend)
    else:
        give_to_a_chat, receive_from_a_chat = getAmountForSingleUser(
            str(request.user), friend)
    return give_to_a_chat, receive_from_a_chat


def getMessagesWithAUser(user, friend):
    groups = getAllGroups()
    cursor = connection.cursor()
    if friend in groups:
        cursor.execute(
            "select * from amount_messages_users_to_group where group_name=%s", [friend])
    else:
        cursor.execute(
            "select * from amount_messages_user_to_user where (sender=%s AND receiver=%s) OR (sender=%s AND receiver=%s)", [user, friend, friend, user])
    return cursor.fetchall()


def login(request):
    if request.method == 'POST':
        name = request.POST['name']
        password = request.POST['password']
        user = auth.authenticate(username=name, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect(home)
        else:
            messages.info(request, 'email/password error')
            return redirect(login)
    else:
        return render(request, 'login.html')


def signup(request):
    if request.method == 'POST':
        name = request.POST['name']
        password1 = request.POST['password']
        email = request.POST['email']
        password2 = request.POST['re_password']
        if name == "" or password1 == "" or password2 == "" or email == "":
            messages.info(request, "please fill up all the fields")
            return redirect('signup')
        elif User.objects.filter(username=name).exists():
            messages.info(request, "user name taken")
            return redirect('signup')
        elif password1 != password2:
            messages.info(request, "password error")
            return redirect('signup')
        elif User.objects.filter(email=email).exists():
            messages.info(request, "email taken")
            return redirect('signup')
        else:
            user = User.objects.create_user(
                username=name, password=password1, email=email)
            user.save()
            auth.login(request, user)
            return redirect(home)
    return render(request, 'signup.html')


def home(request):
    names_of_friends = getNamesOfFriends(str(request.user))
    names_of_groups = getNamesOfGroupsOfUser(str(request.user))
    give, receive = calculateOverallGiveReceives(request)
    give, receive = roundOffTheResult(give, receive)
    return render(request, 'home.html', {'user': str(request.user), 'friends': names_of_friends, 'groups': names_of_groups, 'chat': None, 'give': give, 'receive': receive})


def loadChat(request, friend=None):
    if request.method == 'POST':
        friend = request.POST['temp_text']
    # single chats gives,receives
    give_to_a_chat, receive_from_a_chat = calculateSingleUsersGivesReceives(
        request, friend)
    # overall gives and receives
    give, receive = calculateOverallGiveReceives(request)
    give, receive = roundOffTheResult(give, receive)
    give_to_a_chat, receive_from_a_chat = roundOffTheResult(
        give_to_a_chat, receive_from_a_chat)
    msges_with_names = getMessagesWithAUser(str(request.user), friend)
    names_of_friends = getNamesOfFriends(str(request.user))
    names_of_groups = getNamesOfGroupsOfUser(str(request.user))
    return render(request, 'home.html', {'user': str(request.user), 'friend': friend, 'give': give, 'receive': receive, 'give_to_friend': give_to_a_chat, 'receive_from_friend': receive_from_a_chat, 'friends': names_of_friends, 'groups': names_of_groups, 'chat': 1, 'messages': msges_with_names})


def getUsersForAddingUser(request):
    users = User.objects.all()
    return render(request, 'add_user.html', {'users': users})


def addUserToDb(request):
    friend_name = request.POST['user']
    name = request.user
    cursor = connection.cursor()
    temp_input = friend_name+"_"+str(name)
    cursor.execute(
        "select * from user_to_user_mapping where user_to_user=%s", [temp_input])
    result = cursor.fetchall()
    if len(result) == 0:
        temp_input = str(name)+"_"+friend_name
        cursor.execute(
            "select * from user_to_user_mapping where user_to_user=%s", [temp_input])
        result = cursor.fetchall()
        if len(result) == 0:
            cursor.execute(
                "insert into user_to_user_mapping values(%s)", [temp_input])
    return redirect(home)


def getUsersForAddingGroup(request):
    users = User.objects.all()
    return render(request, 'add_group.html', {'users': users})


def addGroupToDb(request):
    group_name = request.POST['myInput']
    user = str(request.user)
    group_members = request.POST['group_mem']
    group_members = group_members+user
    no_of_group_members = len(getUsersInGroupAsList(group_members))
    cursor = connection.cursor()
    cursor.execute("insert into users_to_group_mapping values(%s,%s,%s)", [
                   group_name, group_members, no_of_group_members])
    return redirect(home)


def saveMsgToDb(request):
    friend = request.POST['temp_text']
    msg = request.POST['msg']
    amnt = request.POST['amnt']
    if(amnt == ""):
        amnt = 0
    cursor = connection.cursor()
    groups = getAllGroups()
    if friend in groups:
        cursor.execute("insert into amount_messages_users_to_group values(%s,%s,%s,%s)", [
            str(request.user), friend, amnt, msg])
    else:
        cursor.execute("insert into amount_messages_user_to_user values(%s,%s,%s,%s)", [
                       str(request.user), friend, amnt, msg])
    return redirect(loadChat, friend=friend)


def removeNameFromString(group_members,user_name):
    friends = group_members.split('_')
    friends.remove(user_name)
    return '_'.join(friends)


def clearChat(request,friend):
    cursor = connection.cursor()
    dbName1 = friend+'_'+str(request.user)
    dbName2 = str(request.user)+'_'+friend
    cursor.execute("delete from user_to_user_mapping where user_to_user=%s or user_to_user=%s",[dbName1,dbName2])
    cursor.execute("delete from amount_messages_user_to_user where (sender=%s and receiver=%s) or (sender=%s and receiver=%s)",[friend,str(request.user),str(request.user),friend])
    #fetch group members then remove user name then update the data in DB
    cursor.execute("select group_members from users_to_group_mapping where group_name=%s",[friend])
    group_members=cursor.fetchall()
    if group_members != []:
        #remove user share from the group
        cursor.execute("delete from amount_messages_users_to_group where sender=%s and group_name=%s",[str(request.user),friend])
        cursor.execute("select count_of_users from users_to_group_mapping where group_name = %s",[friend])
        count = cursor.fetchall()
        count = count[0][0]
        if count == 2:
            cursor.execute("delete from users_to_group_mapping where group_name = %s",[friend])
            cursor.execute("delete from amount_messages_users_to_group where group_name =%s",[friend])
        else:
            cursor.execute("update amount_messages_users_to_group set amount = (amount*(%s-1))/%s",[count,count])
            group_members = removeNameFromString(group_members[0][0],str(request.user))
            cursor.execute("update users_to_group_mapping SET group_members = %s, count_of_users=count_of_users-1 where group_name = %s",[group_members,friend])
    return redirect(home)