from django.urls import path
#urls.py
from . import views
from django.urls import path
from .views import TaskDataAPIView, TaskListView, TaskDetailView
from .views import TaskDeleteView

urlpatterns = [
    path('api/perplexity/', views.perplexity_api, name='perplexity_api'),
    path('', views.index, name='index'),
    path('task/data/', TaskDataAPIView.as_view(), name='task-data-api'),
    path('tasks/', TaskListView.as_view(), name='task-list'),
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
    path('task/<int:pk>/delete/', TaskDeleteView.as_view(), name='task-delete'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('register/',views.register,name='register'),
    path('loginAccount/',views.loginAccount,name='loginAccount'),
    path('chat/',views.chat,name='chat'),
    path('query2flashrag/',views.query2flashrag,name='query2flashrag')
]
