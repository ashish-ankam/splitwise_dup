from django.contrib import admin
from django.urls import path, include
from splitwise import views
urlpatterns = [
    path('', views.login,name="login"),
    path('login',views.login,name="login"),
    path('signup',views.signup,name="signup"),
    path('home',views.home,name="home"),
    path('loadChat/<str:friend>',views.loadChat,name="loadChat"),
    path('getUsersForAddingUser',views.getUsersForAddingUser,name="getUsersForAddingUser"),
    path('getUsersForAddingGroup',views.getUsersForAddingGroup,name="getUsersForAddingGroup"),
    path('addGroupToDb',views.addGroupToDb,name="addGroupToDb"),
    path('addUserToDb',views.addUserToDb,name="addUserToDb"),
    path('saveMsgToDb',views.saveMsgToDb,name="saveMsgToDb"),
    path('clearChat/<str:friend>',views.clearChat,name="clearChat"),
]