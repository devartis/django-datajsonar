from django.conf.urls import url
from django.contrib import messages, admin
from django.contrib.admin import helpers
from django.shortcuts import render, redirect

from django_datajsonar.forms import ScheduleJobForm
from django_datajsonar.models import ReadDataJsonTask
from django_datajsonar.tasks import read_datajson


class AbstractTaskAdmin(admin.ModelAdmin):
    readonly_fields = ('status', 'created', 'finished', 'logs',)
    list_display = ('__unicode__', 'status')

    change_list_template = 'task_change_list.html'

    # Clase del modelo asociado
    model = None

    # Task (callable) a correr asincrónicamente. Por default recible solo una
    # instancia del AbstractTask asociado a este admin, overridear save_model
    # si se quiere otro comportamiento
    task = None

    # String con el fully qualified name del método a llamar cuando
    # se programa una tarea periódica.
    callable_str = None

    def save_model(self, request, obj, form, change):
        super(AbstractTaskAdmin, self).save_model(request, obj, form, change)
        self.task.delay(obj)  # Ejecuta callable

    def add_view(self, request, form_url='', extra_context=None):
        # Bloqueo la creación de nuevos modelos cuando está corriendo la tarea
        if self.model.objects.filter(status=self.model.RUNNING):
            messages.error(request, "Ya está corriendo una tarea")
            return super(AbstractTaskAdmin, self).changelist_view(request, None)

        return super(AbstractTaskAdmin, self).add_view(request, form_url, extra_context)

    def get_urls(self):
        urls = super(AbstractTaskAdmin, self).get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        extra_urls = [url(r'^schedule_task$',
                          self.admin_site.admin_view(self.schedule_task),
                          {'callable_str': self.callable_str},
                          name='%s_%s_schedule_task' % info), ]
        return extra_urls + urls

    def schedule_task(self, request, callable_str):
        form = ScheduleJobForm(initial={'callable': callable_str,
                                        'queue': 'indexing',
                                        'name': self.model._meta.verbose_name_plural})

        context = {
            'title': 'Schedule new task',
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request)
        }

        if request.method == 'POST':
            form = ScheduleJobForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('admin:scheduler_repeatablejob_changelist')

        if callable_str is not None:
            form.fields['callable'].widget.attrs['readonly'] = True
        form.fields['queue'].widget.attrs['readonly'] = True

        context['adminform'] = helpers.AdminForm(form, list([(None, {'fields': form.base_fields})]),
                                                 self.get_prepopulated_fields(request))
        return render(request, 'scheduler.html', context)


@admin.register(ReadDataJsonTask)
class DataJsonAdmin(AbstractTaskAdmin):
    model = ReadDataJsonTask
    task = read_datajson
    callable_str = 'django_datajsonar.tasks.schedule_new_read_datajson_task'

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('indexing_mode',)
        else:
            return self.readonly_fields
