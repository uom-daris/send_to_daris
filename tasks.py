from tardis.tardis_portal.models import Experiment, Dataset, DataFile
from .models import DarisProject
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
        datasets = Dataset.objects.filter(experiments=experiment).order_by('pk')
        daris_project = DarisProject.objects.get(pk=daris_project_id)
        msg = 'connecting to daris'
        logger.warning(msg)
        send_experiment.update_state(state='STARTED', meta={'current_activity': msg})
        cxn = _connect_daris(daris_project)
        logger.warning('connected to daris')
        try:
            for dataset in datasets:
                msg = 'creating zip archive for dataset ' + str(dataset.pk)
                logger.warning(msg)
                send_experiment.update_state(state='STARTED', meta={'current_activity': msg})
                temp_archive = _zip(dataset)
                logger.warning('created zip archive for dataset ' + str(dataset.pk))
                try:
                    msg = 'sending dataset ' + str(dataset.pk) + ' to daris'
                    logger.warning(msg)
                    send_experiment.update_state(state='STARTED', meta={'current_activity': msg})
                    _send_dataset(cxn, dataset, temp_archive, host_addr, daris_project, async=False)
                    logger.warning('sent dataset ' + str(dataset.pk) + ' to daris')
                finally:
                    msg = 'removing temporary file: ' + temp_archive
                    logger.warning(msg)
                    send_experiment.update_state(state='STARTED', meta={'current_activity': msg})
                    os.remove(temp_archive)
                    logger.warning('removed temporary file: ' + temp_archive)
        finally:
            logger.warning('disconnecting daris')
            cxn.disconnect()
            logger.warning('disconnected daris')
    except:
        raise


@task(name='send_dataset_to_daris')
def send_dataset(dataset_id, daris_project_id, host_addr):
    try:
        dataset = Dataset.objects.get(pk=dataset_id)
        daris_project = DarisProject.objects.get(pk=daris_project_id)
        msg = 'creating zip archive for dataset ' + str(dataset_id)
        logger.warning(msg)
        send_dataset.update_state(state='STARTED', meta={'current_activity': msg})
        temp_archive = _zip(dataset)
        logger.warning('created zip archive for dataset ' + str(dataset_id))
        try:
            msg = 'connecting to daris'
            logger.warning(msg)
            send_dataset.update_state(state='STARTED', meta={'current_activity': msg})
            cxn = _connect_daris(daris_project)
            logger.warning('connected to daris')
            try:
                msg = 'sending dataset ' + str(dataset.pk) + ' to daris'
                logger.warning(msg)
                send_dataset.update_state(state='STARTED', meta={'current_activity': msg})
                _send_dataset(cxn, dataset, temp_archive, host_addr, daris_project, async=True)
                logger.warning('sent dataset ' + str(dataset.pk) + ' to daris')
            finally:
                logger.warning('disconnecting daris')
                cxn.disconnect()
                logger.warning('disconnected daris')
        finally:
            msg = 'removing temporary file: ' + temp_archive
            logger.warning(msg)
            send_dataset.update_state(state='STARTED', meta={'current_activity': msg})
            os.remove(temp_archive)
            logger.warning('removed temporary file: ' + temp_archive)
    except:
        raise


@task(name='send_datafile_to_daris')
def send_datafile(datafile_id, daris_project_id, host_addr):
    try:
        datafile = DataFile.objects.get(pk=datafile_id)
        daris_project = DarisProject.objects.get(pk=daris_project_id)
        logger.warning('connecting to daris')
        cxn = _connect_daris(daris_project)
        logger.warning('connected to daris')
        try:
            logger.warning('sending datafile ' + datafile.filename + ' to daris')
            _send_datafile(cxn, datafile, host_addr, daris_project)
            logger.warning('sent datafile ' + datafile.filename + ' to daris')
        finally:
            logger.warning('disconnecting daris')
            cxn.disconnect()
            logger.warning('disconnected daris')
    except:
        raise


def _zip(dataset, func=None):
    _, path = tempfile.mkstemp('.zip', 'send_dataset_' + str(dataset.pk) + '_to_daris_', )
    with WZipFile(path, 'w', ZIP_STORED, allowZip64=True) as wzipfile:
        datafiles = DataFile.objects.filter(dataset=dataset)
        for datafile in datafiles:
            if not func or (func and func(datafile)):
                with datafile.file_object as file_object:
                    arcname = os.path.join(datafile.directory if datafile.directory else '', datafile.filename)
                    wzipfile.writeobj(file_object, datafile.size, arcname, date_time=datafile.modification_time)
    return path


def _send_dataset(cxn, dataset, archive, host_addr, daris_project, async=True, dicom_ingest=True):
    experiment = dataset.get_first_experiment()
    w = mfclient.XmlStringWriter('args')
    w.push('experiment')
    w.add('id', experiment.pk)
    if experiment.title:
        w.add('title', experiment.title)
    if experiment.description:
        w.add('description', experiment.description)
    w.pop()
    w.push('dataset')
    w.add('id', dataset.pk)
    if dataset.description:
        w.add('description', dataset.description)
    if dataset.instrument:
        w.add('instrument', dataset.instrument)
    w.pop()
    w.add('source-mytardis-uri', host_addr)
    w.add('project', daris_project.cid)
    w.add("dicom-ingest", dicom_ingest)
    w.add("async", async)
    input1 = mfclient.MFInput(archive, 'application/zip')
    cxn.execute('daris.mytardis.dataset.import', w.doc_text(), [input1])


def _send_datafile(cxn, datafile, host_addr, daris_project):
    raise NotImplementedError(
        'Sending individual data file to DaRIS has not yet been implemented. Nor is enabled in MyTardis portal.')


def _connect_daris(daris_project):
    daris_server = daris_project.server
    cxn = mfclient.MFConnection(daris_server.host, daris_server.port, daris_server.transport.lower() == 'https')
    cxn.connect(token=daris_project.token)
    return cxn
