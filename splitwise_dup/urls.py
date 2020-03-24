from django.contrib import admin
from django.urls import path, include
from . import views
urlpatterns = [
    path('', views.login,name="login"),
    path('login',views.login,name="login"),
    path('signup',views.signup,name="signup"),
    path('home',views.home,name="home"),
    path('chat',views.chat,name="chat"),
    path('addUser',views.addUser,name="addUser"),
    path('addToDb',views.addToDb,name="addToDb"),
]