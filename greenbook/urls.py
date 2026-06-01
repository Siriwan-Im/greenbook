from django.contrib import admin
from django.urls import path
from . import views


urlpatterns = [
    path('signin', views.signin, name='signin'),
    path('login',views.login , name='login'),
    path('home', views.home, name='home'),
    path('viewside', views.viewside, name='viewside'),
    path('logout', views.logout, name='logout'),
    path('predict', views.predict_view, name='predict'),
    path("predict-options/", views.predict_option, name="predict_option"),
    path("predict-price/", views.predict_price, name="predict_price"),
    path('branch-predict', views.branch_predict_view, name='branch-predict'),
    path("branch-predict-options/", views.branch_predict_option, name="branch_predict_option"),
    path("branch-predict-price/", views.branch_predict_price, name="branch_predict_price"),
    path('seasonal-predict', views.seasonal_predict_view, name='seasonal-predict'),
    path("seasonal-predict-options/", views.seasonal_predict_option, name="seasonal_predict_option"),
    path("seasonal-predict-price/", views.seasonal_predict_price, name="seasonal_predict_price"),
]