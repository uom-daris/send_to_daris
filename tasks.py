from tardis.tardis_portal.models import Experiment, Dataset, DataFile
from .models import DarisProject
from .models import DarisServer
from celery.utils.log import get_task_logger
from celery.task import task

import tempfile
from .wzipfile import WZipFile
from zipfile import ZIP_STORED
import os

import mfclient

logger = get_task_logger(__name__)


@task(name='send_experiment_to_daris')
def send_experiment(experiment_id, daris_project_id, host_addr):
    try:
        experiment = Experiment.objects.get(pk=experiment_id)
        datasets = Dataset.objects.filter(experiments=experiment)
        thandle, tpath = _create_temp_file('experiment', experiment_id)
        logger.warning('src: ' + _generate_experiment_source_url(host_addr, experiment))
        try:
            with WZipFile(tpath, 'w', ZIP_STORED, allowZip64=True) as wzipfile:
                for dataset in datasets:
                    logger.warning('src: ' + _generate_dataset_source_url(host_addr, dataset))
                    datafiles = DataFile.objects.filter(dataset=dataset)
                    for datafile in datafiles:
                        logger.warning('src: ' + _generate_datafile_source_url(host_addr, datafile))
                        _add_to_zipfile(wzipfile, datafile)
            logger.warning('created zip file: ' + tpath)
            send_experiment.update_state(state='EXECUTING', meta={'progress': 'created zip file.'})
            # send_experiment.backend.mark_as_started(send_experiment.request.id, progress=100)
            # TODO
        finally:
            if tpath:
                logger.warning('deleting zip file: ' + tpath)
                os.remove(tpath)
    except:
        raise


@task(name='send_dataset_to_daris')
def send_dataset(dataset_id, daris_project_id, host_addr):
    try:
        thandle, tpath = _create_temp_file('dataset', dataset_id)
        try:
            with WZipFile(tpath, 'w', ZIP_STORED, allowZip64=True) as wzipfile:
                dataset = Dataset.objects.get(pk=dataset_id)
                datafiles = DataFile.objects.filter(dataset=dataset)
                for datafile in datafiles:
                    _add_to_zipfile(wzipfile, datafile)
            logger.warning('created zip file: ' + tpath)
            # TODO
        finally:
            if tpath:
                logger.warning('deleting zip file: ' + tpath)
                os.remove(tpath)
    except:
        raise


@task(name='send_datafile_to_daris')
def send_datafile(datafile_id, daris_project_id, host_addr):
    try:
        thandle, tpath = _create_temp_file('datafile', datafile_id)
        try:
            with WZipFile(tpath, 'w', ZIP_STORED, allowZip64=True) as wzipfile:
                datafile = DataFile.objects.get(pk=datafile_id)
                _add_to_zipfile(wzipfile, datafile)
            logger.warning('created zip file: ' + tpath)
            # TODO
        finally:
            if tpath:
                logger.warning('deleting zip file: ' + tpath)
                os.remove(tpath)
    except:
        raise


def _create_temp_file(object_type, object_id):
    return tempfile.mkstemp('.zip', 'send_' + object_type + '_' + object_id + '_to_daris_', )


def _generate_experiment_source_url(host_addr, experiment):
    return host_addr + '/' + _generate_experiment_path(experiment)


def _generate_dataset_source_url(host_addr, dataset):
    return host_addr + '/' + _generate_dataset_path(dataset)


def _generate_datafile_source_url(host_addr, datafile):
    return host_addr + '/' + _generate_datafile_path(datafile)


def _generate_experiment_path(experiment):
    return 'experiment-' + str(experiment.pk)


def _generate_dataset_path(dataset):
    experiment = dataset.get_first_experiment()
    return os.path.join(_generate_experiment_path(experiment), 'dataset-' + str(dataset.pk))


def _generate_datafile_path(datafile):
    dataset = datafile.dataset
    return os.path.join(_generate_dataset_path(dataset),
                        datafile.directory if datafile.directory else '', datafile.filename)


def _add_to_zipfile(wzipfile, datafile):
    with datafile.file_object as file_object:
        wzipfile.writeobj(file_object, datafile.size, _generate_datafile_path(datafile),
                          date_time=datafile.modification_time)


def _create_daris_dataset(daris_project_id):
    daris_project = DarisProject.objects.get(pk=daris_project_id)
    daris_server = daris_project.server


def _connect_daris(daris_project_id):
    daris_project = DarisProject.objects.get(pk=daris_project_id)
    daris_server = daris_project.server
    cxn = mfclient.MFConnection(daris_server.host, daris_server.port, daris_server.transport.lower() == 'https')
    cxn.connect(token=daris_project.token)
    return cxn

