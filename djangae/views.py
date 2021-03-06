import os
import logging
from importlib import import_module

from django.conf import settings
from django.http import HttpResponse, HttpResponseServerError
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from djangae.utils import on_production


def warmup(request):
    """
        Provides default procedure for handling warmup requests on App
        Engine. Just add this view to your main urls.py.
    """
    for app in settings.INSTALLED_APPS:
        for name in ('urls', 'views', 'models'):
            try:
                import_module('%s.%s' % (app, name))
            except ImportError:
                pass
    content_type = 'text/plain; charset=%s' % settings.DEFAULT_CHARSET
    return HttpResponse("Warmup done.", content_type=content_type)


@csrf_exempt
def deferred(request):
    from google.appengine.ext.deferred.deferred import (
        run,
        SingularTaskFailure,
        PermanentTaskFailure
    )

    response = HttpResponse()

    if 'HTTP_X_APPENGINE_TASKEXECUTIONCOUNT' in request.META:
        logging.debug("[DEFERRED] Retry %s of deferred task", request.META['HTTP_X_APPENGINE_TASKEXECUTIONCOUNT'])

    if 'HTTP_X_APPENGINE_TASKNAME' not in request.META:
        logging.critical('Detected an attempted XSRF attack. The header "X-AppEngine-Taskname" was not set.')
        response.status_code = 403
        return response

    in_prod = on_production()

    if in_prod and os.environ.get("REMOTE_ADDR") != "0.1.0.2":
        logging.critical('Detected an attempted XSRF attack. This request did not originate from Task Queue.')
        response.status_code = 403
        return response

    try:
        run(request.body)
    except SingularTaskFailure:
        logging.debug("Failure executing task, task retry forced")
        response.status_code = 408
    except PermanentTaskFailure:
        logging.exception("Permanent failure attempting to execute task")

    return response


@csrf_exempt
@require_POST
def internalupload(request):
    try:
        return HttpResponse(str(request.FILES['file'].blobstore_info.key()))
    except Exception:
        logging.exception("DJANGAE UPLOAD FAILED: The internal upload handler couldn't retrieve the blob info key.")
        return HttpResponseServerError()
