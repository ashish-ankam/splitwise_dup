from django.contrib import admin
from django.urls import path, include
from splitwise import views
urlpatterns = [
    path('', views.login,name="login"),
    path('login',views.login,name="login"),
    path('signup',views.signup,name="signup"),
    path('home',views.home,name="home"),
    path('loadChat/<str:friend>',views.loadChat,name="loadChat"),
    path('getUsersForUser',views.getUsersForUser,name="getUsersForUser"),
    path('getUsersForGroup',views.getUsersForGroup,name="getUsersForUroup"),
    path('addGroupToDb',views.addGroupToDb,name="addGroupToDb"),
    path('addUserToDb',views.addUserToDb,name="addUserToDb"),
    path('saveMsgToDb',views.saveMsgToDb,name="saveMsgToDb"),
]