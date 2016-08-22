from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from tardis.tardis_portal.auth import decorators as authz
from django.http import HttpResponse
from django.http import JsonResponse
from django.template import loader
from tardis.tardis_portal.models import Experiment, Dataset, DataFile
from .models import DarisProject
from . import tasks
from celery.result import AsyncResult
import json


@login_required
@authz.experiment_download_required
def send_experiment(request, experiment_id, daris_project_id=None):
    return _send_to_daris(request, 'experiment', experiment_id, daris_project_id)


@login_required
@authz.dataset_download_required
def send_dataset(request, dataset_id, daris_project_id=None):
    return _send_to_daris(request, 'dataset', dataset_id, daris_project_id)


@login_required
@authz.datafile_access_required
def send_datafile(request, datafile_id, daris_project_id=None):
    return _send_to_daris(request, 'datafile', datafile_id, daris_project_id)


def _send_to_daris(request, object_type, object_id, daris_project_id=None):
    host_addr = 'https://' if request.is_secure() else 'http://'
    host_addr += request.get_host()
    if daris_project_id:
        template = loader.get_template('send-to-daris/task-monitor.html')
        daris_project = DarisProject.objects.get(pk=daris_project_id)
        if object_type == 'experiment':
            prefix = reverse(send_experiment, kwargs={'experiment_id': object_id})
            result = tasks.send_experiment.delay(object_id, daris_project_id, host_addr)
            obj = Experiment.objects.get(pk=object_id)
        elif object_type == 'dataset':
            prefix = reverse(send_dataset, kwargs={'dataset_id': object_id})
            result = tasks.send_dataset.delay(object_id, daris_project_id, host_addr)
            obj = Dataset.objects.get(pk=object_id)
        else:
            prefix = reverse(send_datafile, kwargs={'datafile_id': object_id})
            result = tasks.send_datafile.delay(object_id, daris_project_id, host_addr)
            obj = DataFile.objects.get(pk=object_id)
        context = {
            'url_prefix': prefix,
            'object_type': object_type,
            'object': obj,
            'daris_project': daris_project,
            'task_id': result.id,
        }
    else:
        template = loader.get_template('send-to-daris/project-selector.html')
        context = {
            'object_type': object_type,
            'object_id': object_id,
            'daris_project_list': DarisProject.objects.all(),
        }
    return HttpResponse(template.render(context, request))


@login_required
def task_status(request):
    task_id = request.GET['task_id']
    task = AsyncResult(task_id)
    return HttpResponse(json.dumps({'state': task.state, 'info': task.result if task.result else None}),
                        content_type='application/json')
