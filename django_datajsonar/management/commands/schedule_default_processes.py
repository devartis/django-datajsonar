#! coding: utf-8

from django.core.management import BaseCommand
from django.conf import settings

from django_datajsonar.models import Synchronizer, Stage


class Command(BaseCommand):

    def handle(self, *args, **options):
        processes = getattr(settings, 'DEFAULT_PROCESSES', [])
        for process in processes:
            next_stage = None
            for stage in process['stages'][::-1]:
                next_stage, _ = Stage.objects.update_or_create(name=stage['name'],
                                                               callable_str=stage['callable_str'],
                                                               queue=stage['queue'],
                                                               task=stage.get('task', ''),
                                                               defaults={'next_stage': next_stage})

            Synchronizer.objects.update_or_create(name=process['name'],
                                                  defaults={'start_stage': next_stage})
