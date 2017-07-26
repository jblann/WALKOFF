import json
from flask import Blueprint, Response
from core.case.callbacks import WorkflowShutdown, FunctionExecutionSuccess, StepExecutionError
from datetime import datetime

workflowresults_page = Blueprint('workflowresults_page', __name__)


def __workflow_shutdown_event_generator():
    while True:
        data = yield
        yield 'data: %s\n\n' % data


def __workflow_steps_event_generator():
    while True:
        data = yield
        yield 'data: %s\n\n' % data

__workflow_shutdown_event_stream = __workflow_shutdown_event_generator()
__workflow_steps_event_stream = __workflow_shutdown_event_generator()
__workflow_shutdown_event_stream.send(None)
__workflow_steps_event_stream.send(None)


@WorkflowShutdown.connect
def __workflow_ended_callback(sender, **kwargs):
    data = 'None'
    if 'data' in kwargs:
        data = kwargs['data']
        if not isinstance(data, str):
            data = str(data)
    result = {'name': sender.name,
              'timestamp': str(datetime.utcnow()),
              'result': data}
    __workflow_shutdown_event_stream.send(json.dumps(result))


@FunctionExecutionSuccess.connect
def __step_ended_callback(sender, **kwargs):
    data = 'None'
    step_input = str(sender.input)
    if 'data' in kwargs:
        data = kwargs['data']
        if not isinstance(data, str):
            data = str(data)
    result = {'name': sender.name,
              'type': "SUCCESS",
              'input': step_input,
              'result': data}
    __workflow_steps_event_stream.send(json.dumps(result))


@StepExecutionError.connect
def __step_error_callback(sender, **kwargs):
    result = {'name': sender.name, 'type': 'ERROR'}
    if 'data' in kwargs:
        data = kwargs['data']
        result['input'] = data['input']
        result['result'] = data['result']
    __workflow_steps_event_stream.send(json.dumps(result))


@workflowresults_page.route('/stream', methods=['GET'])
def stream_workflow_success_events():
    return Response(__workflow_shutdown_event_stream, mimetype='text/event-stream')


@workflowresults_page.route('/stream-steps', methods=['GET'])
# @auth_token_required
# @roles_accepted(*running_context.user_roles['/playbooks'])
def stream_workflow_step_events():
    return Response(__workflow_steps_event_stream, mimetype='text/event-stream')
