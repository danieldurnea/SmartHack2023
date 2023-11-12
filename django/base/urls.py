
from django.urls import path 
from . import views 
  
urlpatterns = [ 
    path("", views.home, name="home"),
    path("input", views.main_page, name = "main_page"),
    path("comparison", views.comparison, name="comparison"),
    path("get_other", views.get_other, name="get_other"),
    path("compare_companies", views.compare_companies, name="compare_companies"),
]
