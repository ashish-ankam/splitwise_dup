from django.contrib import admin
from django.urls import path, include
from splitwise import views
urlpatterns = [
    path('', views.login,name="login"),
    path('login',views.login,name="login"),
    path('signup',views.signup,name="signup"),
    path('home',views.home,name="home"),
    path('amountForChat/',views.amountForChat,name="amountForChat"),
    path('loadChat/',views.loadChat,name="loadChat"),
    path('getAddUserTemplate/',views.getAddUserTemplate,name = "getAddUserTemplate"),
    path('getAddGrpTemplate/',views.getAddGrpTemplate,name = "getAddGrpTemplate"),
    path('getUsers/',views.getUsersForAddingUser,name="getUsersForAddingUser"),
    path('addGroupToDb',views.addGroupToDb,name="addGroupToDb"),
    path('addUserToDb',views.addUserToDb,name="addUserToDb"),
    path('saveMsgToDb',views.saveMsgToDb,name="saveMsgToDb"),
    path('clearChat/',views.clearChat,name="clearChat"),
    path('groupGivings/',views.groupGivings,name="groupGivings"),
    path('getNewMsges/',views.getNewMsges,name="getNewMsges"),
    path('getOlderMsges/',views.getOlderMsges,name="getOlderMsges"),
]