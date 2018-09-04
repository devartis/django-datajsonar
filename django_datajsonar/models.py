#! coding: utf-8
from __future__ import unicode_literals
from importlib import import_module

from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.core.files.storage import default_storage
from django.db import models, transaction
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

from django_rq import get_queue


class Metadata(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "Metadatos enriquecidos"

    key = models.CharField(max_length=64)
    value = models.TextField()

    # Generic foreign key magics
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()


class Catalog(models.Model):
    title = models.CharField(max_length=200)
    identifier = models.CharField(max_length=200, unique=True)
    metadata = models.TextField()
    present = models.BooleanField(default=True)
    updated = models.BooleanField(default=True)
    error = models.BooleanField(default=False)
    new = models.BooleanField(default=False)

    enhanced_meta = GenericRelation(Metadata, null=True)

    def __unicode__(self):
        return u'%s (%s)' % (self.title, self.identifier)

    def __str__(self):
        return self.__unicode__()


class Dataset(models.Model):

    REVIEWED = "REVIEWED"
    ON_REVISION = "ON_REVISION"
    NOT_REVIEWED = "NOT_REVIEWED"

    REVIEWED_STATUS = (
        (REVIEWED, "Revisado"),
        (ON_REVISION, "En revisión"),
        (NOT_REVIEWED, "No revisado"),
    )

    title = models.CharField(max_length=200)
    identifier = models.CharField(max_length=200)
    metadata = models.TextField()
    catalog = models.ForeignKey(to=Catalog, on_delete=models.CASCADE)
    indexable = models.BooleanField(default=False)
    present = models.BooleanField(default=True)
    updated = models.BooleanField(default=True)
    error = models.BooleanField(default=False)
    new = models.BooleanField(default=False)
    reviewed = models.CharField(max_length=20, choices=REVIEWED_STATUS, default=NOT_REVIEWED)
    last_reviewed = models.DateField(null=True, blank=True, default=None)

    themes = models.TextField(blank=True, null=True)

    enhanced_meta = GenericRelation(Metadata)

    def __unicode__(self):
        return u'%s (%s)' % (self.identifier, self.catalog.identifier)

    def __str__(self):
        return self.__unicode__()


def filepath(instance, _):
    """Método para asignar el nombre al archivo fuente del FileField
    del modelo Distribution
    """
    return u'distribution_raw/{}.csv'.format(instance.identifier)


def get_distribution_storage():
    """Importa dinámicamente el módulo configurado en el setting
    DATAJSON_AR_DISTRIBUTION_STORAGE, y devuelve una instancia
    del objeto determinado. De no existir, devuelve el storage default
    """
    data_file_storage_path = getattr(settings, 'DATAJSON_AR_DISTRIBUTION_STORAGE', None)
    if data_file_storage_path is None:
        return default_storage

    split = data_file_storage_path.split('.')
    module = import_module('.'.join(split[:-1]))

    storage = getattr(module, split[-1], None)
    if storage is None:
        raise ImproperlyConfigured

    return storage()


class Distribution(models.Model):
    identifier = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    metadata = models.TextField()
    dataset = models.ForeignKey(to=Dataset, on_delete=models.CASCADE)
    download_url = models.URLField(max_length=1024, null=True)
    data_hash = models.CharField(max_length=128, default='')
    last_updated = models.DateTimeField(blank=True, null=True)

    data_file = models.FileField(
        storage=get_distribution_storage(),
        max_length=2000,
        upload_to=filepath,
        blank=True
    )
    present = models.BooleanField(default=True)
    updated = models.BooleanField(default=True)
    error = models.BooleanField(default=False)

    enhanced_meta = GenericRelation(Metadata)
    new = models.BooleanField(default=False)

    def __unicode__(self):
        return u'%s (%s)' % (self.identifier, self.dataset.catalog.identifier)

    def __str__(self):
        return self.__unicode__()


class Field(models.Model):
    title = models.CharField(max_length=200, null=True)
    identifier = models.CharField(max_length=200, null=True)
    metadata = models.TextField()
    distribution = models.ForeignKey(to=Distribution, on_delete=models.CASCADE)
    present = models.BooleanField(default=True)
    updated = models.BooleanField(default=True)
    error = models.BooleanField(default=False)

    enhanced_meta = GenericRelation(Metadata)
    new = models.BooleanField(default=False)

    def __unicode__(self):
        return u'%s (%s)' %\
               (self.title or 'Field sin title',
                self.distribution.dataset.catalog.identifier)

    def __str__(self):
        return self.__unicode__()


class BaseRegisterFile(models.Model):
    """Base de los archivos de registro de datasets y de nodos.
    Contiene atributos de estado del archivo y fechas de creado / modificado
    """
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"

    STATE_CHOICES = (
        (UPLOADED, "Cargado"),
        (PROCESSING, "Procesando"),
        (PROCESSED, "Procesado"),
        (FAILED, "Error"),
    )

    created = models.DateTimeField()
    modified = models.DateTimeField(null=True)
    indexing_file = models.FileField(upload_to='register_files/')
    uploader = models.ForeignKey(User)
    state = models.CharField(max_length=20, choices=STATE_CHOICES)
    logs = models.TextField(default=u'-')

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.pk:  # first time only
            self.created = timezone.now()
            self.state = self.UPLOADED

        super(BaseRegisterFile, self).save(force_insert, force_update, using, update_fields)


class NodeRegisterFile(BaseRegisterFile):
    def __unicode__(self):
        return "Node register file: {}".format(self.created)

    def __str__(self):
        return self.__unicode__()


class DatasetIndexingFile(BaseRegisterFile):
    def __unicode__(self):
        return "Indexing file: {}".format(self.created)

    def __str__(self):
        return self.__unicode__()


class Node(models.Model):

    catalog_id = models.CharField(max_length=100, unique=True)
    catalog_url = models.URLField()
    indexable = models.BooleanField()
    catalog = models.TextField(default='{}')
    admins = models.ManyToManyField(User, blank=True)

    def __unicode__(self):
        return self.catalog_id

    def __str__(self):
        return self.__unicode__()


class AbstractTask(models.Model):

    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"

    STATUS_CHOICES = (
        (RUNNING, "Procesando catálogos"),
        (FINISHED, "Finalizada"),
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created = models.DateTimeField()
    finished = models.DateTimeField(null=True)
    logs = models.TextField()
    stage = GenericRelation('Stage', content_type_field='task')

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.pk:  # first time only
            self.created = timezone.now()
            self.status = self.RUNNING

        super(AbstractTask, self).save(force_insert, force_update, using, update_fields)

    def __unicode__(self):
        return "Task at %s" % self._format_date(self.created)

    def __str__(self):
        return self.__unicode__()

    def _format_date(self, date):
        return timezone.localtime(date).strftime(self.DATE_FORMAT)

    @classmethod
    def info(cls, task, msg):
        with transaction.atomic():
            task = cls.objects.select_for_update().get(id=task.id)
            task.logs += msg + '\n'
            task.save()

    class Meta:
        abstract = True


class ReadDataJsonTask(AbstractTask):
    COMPLETE_RUN = True
    METADATA_ONLY = False
    INDEXING_CHOICES = ((COMPLETE_RUN, 'Corrida completa'), (METADATA_ONLY, 'Corrida solo de metadatos'),)
    default_mode = getattr(settings, 'DATAJSON_AR_DOWNLOAD_RESOURCES', True)
    indexing_mode = models.BooleanField(choices=INDEXING_CHOICES, default=default_mode)


class Stage(models.Model):

    ACTIVE = True
    INACTIVE = False

    STATUS_CHOICES = (
        (ACTIVE, "Tarea activa"),
        (INACTIVE, "Tarea inactiva"),
    )

    status = models.BooleanField(default=False, choices=STATUS_CHOICES)
    callable_str = models.CharField(max_length=100)
    queue = models.CharField(max_length=50)
    next_stage = models.ForeignKey('self', null=True, blank=True)

    # Generic foreign key magics
    task = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('task', 'object_id')

    def close_task_if_finished(self):
        if not get_queue(self.queue).jobs:
            self.content_object.status = self.content_object.FINISHED
            self.content_object.save()
            finished = True
        else:
            finished = False

        return finished

    def __unicode__(self):
        return u'Stage' + str(self.pk)

    def __str__(self):
        return self.__unicode__()


class Synchronizer(models.Model):

    RUNNING = True
    STAND_BY = False

    STATUS_CHOICES = (
        (RUNNING, "Corriendo procesos"),
        (STAND_BY, "En espera"),
    )

    status = models.BooleanField(default=False, choices=STATUS_CHOICES)

    start_stage = models.ForeignKey(to=Stage, related_name='synchronizer')
    actual_stage = models.ForeignKey(to=Stage, related_name='running_synchronizer', null=True, blank=True)

    def begin_stage(self, stage=None):
        stage = stage or self.start_stage
        stage.status = Stage.ACTIVE
        task = self.run_callable(stage.callable_str)
        stage.content_object = task
        stage.object_id = task.pk
        stage.save()
        self.actual_stage = stage
        self.save()

    def check_completion(self):
        finished = False
        if self.actual_stage.close_task_if_finished():
            self.actual_stage.status = self.actual_stage.INACTIVE
            self.actual_stage.save()
            if self.actual_stage.next_stage is None:
                finished = True
            else:
                self.begin_stage(self.actual_stage.next_stage)
        return finished

    def run_callable(self, callable_str):
        split = callable_str.split('.')
        module = import_module('.'.join(split[:-1]))
        method = getattr(module, split[-1], None)
        return method()

    def __unicode__(self):
        return u'Synchro' + str(self.pk)

    def __str__(self):
        return self.__unicode__()
