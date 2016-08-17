from django.conf.urls import url
from . import views

urlpatterns = [url(r'^experiment/(?P<experiment_id>\d+)/$', views.send_experiment, name='send-experiement'),
               url(r'^experiment/(?P<experiment_id>\d+)/to/project/(?P<daris_project_id>\d+)/$',
                   views.send_experiment, name='send-experiment-to-daris'),
               url(r'^dataset/(?P<dataset_id>\d+)/$', views.send_dataset, name='send-dataset'),
               url(r'^dataset/(?P<dataset_id>\d+)/to/project/(?P<daris_project_id>\d+)/$',
                   views.send_dataset, name='send-dataset-to-daris'),
               url(r'^datafile/(?P<datafile_id>\d+)/$', views.send_datafile, name='send-datafile'),
               url(r'^datafile/(?P<datafile_id>\d+)/to/project/(?P<daris_project_id>\d+)/$',
                   views.send_datafile, name='send-datafile-to-daris'),
               url(r'^task-status/$', views.task_status, name='task-status')]
