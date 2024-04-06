from flask import Flask as fl, jsonify, request
import time
import datetime
import logging
import os
import requests

app = fl(__name__)

# global variables
todos = []
id_counter = 1
request_counter = 1


# Delete previous log file if it exists
def create_log_file():
    if os.path.exists("logs/requests.log"):
        os.remove("logs/requests.log")
    if os.path.exists('logs/todos.log'):
        os.remove('logs/todos.log')

    # formatter for the request logger and the todo logger


formatter1 = logging.Formatter('%(asctime)s.%(msecs)03d %(levelname)s : %(message)s | request: #%(request_number)s',
                               datefmt='%d-%m-%Y %H:%M:%S')

# create request_logger
request_logger = logging.getLogger('request-logger')
request_logger.setLevel(logging.INFO)
handler1 = logging.FileHandler('logs/requests.log')
handler1.setLevel(logging.INFO)
handler1.setFormatter(formatter1)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter1)
request_logger.addHandler(stream_handler)
request_logger.addHandler(handler1)

# create todo_logger
todo_logger = logging.getLogger('todo-logger')
todo_logger.setLevel(logging.INFO)
handler2 = logging.FileHandler('logs/todos.log')
handler2.setLevel(logging.DEBUG)
handler2.setFormatter(formatter1)
todo_logger.addHandler(handler2)


# add handlers to loggers
def handle_request(resource_name, http_verb, duration_ms):
    global request_counter
    now = datetime.datetime.now()
    request_logger.info(
        f'Incoming request | #{request_counter} | resource: {resource_name} | HTTP Verb {http_verb.upper()}',
        extra={'request_number': request_counter})
    request_logger.debug(f'request #{request_counter} duration: {duration_ms}ms',
                         extra={'request_number': request_counter})
    request_counter += 1


@app.route('/todo/health', methods=['GET'])  # this is the route for the health check
def getReturn():
    start_time = time.time()
    end_time = time.time()
    handle_request("/todo/health", "GET", end_time - start_time)
    return 'OK'


@app.route('/todo', methods=['POST'])
def create_todo():  # this is the route for creating a new todo
    start_time = time.time()
    global id_counter  # this is the global variable that will be used to create a new id for the todo
    data = request.json
    title = data.get('title')
    content = data.get('content')
    due_date = data.get('dueDate')

    # check if the title is already in the system or the due date is in the past
    for todo in todos:
        if (todo['title'] == title):
            todo_logger.error("Error: TODO with the title [" + title + "] already exists in the system",
                              extra={'request_number': request_counter})
            return jsonify({'errorMessage': f'Error: TODO with the title {title} already exists in the system'}), 409

    # check if due date is in the past

    due_date_seconds = float(due_date) / 1000  # convert millis to seconds
    current_time_seconds = time.time()
    if due_date_seconds < current_time_seconds:
        todo_logger.error("Error: Can't create new TODO that its due date is in the past",
                          extra={'request_number': request_counter})
        return jsonify({'errorMessage': 'Error: Can\'t create new TODO that its due date is in the past'}), 409

    todo = {
        'id': id_counter,
        'title': title,
        'content': content,
        'dueDate': due_date,
        'status': 'PENDING'
    }

    todos.append(todo)
    id_counter += 1

    todo_logger.info("Creating new TODO with Title [" + title + "]", extra={
        'request_number': request_counter})
    todo_logger.debug("Currently there are " + str(len(todos) - 1) +
                      " Todos in the system. New TODO will be assigned with id " + str(id_counter - 1),
                      extra={'request_number': request_counter})

    end_time = time.time()
    handle_request('/todo', 'POST', end_time - start_time)  # log the request

    return jsonify({'result': todo['id']}), 200


@app.route('/todo/size', methods=['GET'])
def get_todos_size():
    start_time = time.time()
    status = request.args.get('status')
    returnTodos = []  # this is the list that will be returned

    if (status == 'ALL'):
        returnTodos = todos
    elif (status == 'PENDING'):
        returnTodos = [todo for todo in todos if todo['status'] == 'PENDING']
    elif (status == 'LATE'):
        returnTodos = [todo for todo in todos if todo['status'] == 'LATE']
    elif (status == 'DONE'):
        returnTodos = [todo for todo in todos if todo['status'] == 'DONE']
    else:
        end_time = time.time()
        handle_request('/todo/size', 'GET', end_time - start_time)  # log the request
        todo_logger.error('Error: Invalid input', extra={'request_number': request_counter})
        return jsonify({'errorMessage': 'Error: Invalid input'}), 400

    todo_logger.info('Total TODOs count for state ' + status + ' is ' + str(len(returnTodos)),
                     extra={'request_number': request_counter})

    end_time = time.time()
    handle_request('/todo/size', 'GET', end_time - start_time)  # log the request

    return jsonify({'result': len(returnTodos)}), 200


@app.route('/todo/content', methods=['GET'])
def get_todos():
    start_time = time.time()
    returnTodos = []
    sortedTodos = []

    status = request.args.get('status', default='ALL', type=str)
    sortBy = request.args.get('sortBy', default='ID', type=str)
    todo_logger.info('Extracting todos content. Filter: ' + status + ' | Sorting by: ' + sortBy,
                     extra={'request_number': request_counter})

    # check if the status or sortBy is valid
    if (sortBy != 'ID' and sortBy != 'DUE_DATE' and sortBy != 'TITLE'):
        end_time = time.time()
        handle_request('/todo', 'GET', end_time - start_time)  # log the request
        todo_logger.error('Error: Invalid input', extra={'request_number': request_counter})
        return jsonify({'errorMessage': 'Error: Invalid input'}), 400

    if (status != 'ALL' and status != 'PENDING' and status != 'LATE' and status != 'DONE'):
        end_time = time.time()
        handle_request('/todo', 'GET', end_time - start_time)  # log the request
        todo_logger.error('Error: Invalid input', extra={'request_number': request_counter})
        return jsonify({'errorMessage': 'Error: Invalid input'}), 400

    if (status == 'ALL'):
        returnTodos = todos
    else:
        returnTodos = [todo for todo in todos if todo['status'] == status]

    sortedTodos = sorted(returnTodos, key=lambda i: i[sortBy.lower()])  # sort the list by the given parameter
    todo_logger.debug('There are a total of ' + str(len(todos)) + ' todos in the system. The result holds ' + str(
        len(sortedTodos)) + ' todos', extra={'request_number': request_counter})

    end_time = time.time()
    handle_request('/todo/conntent', 'GET', end_time - start_time)  # log the request

    return jsonify({'result': sortedTodos}), 200


@app.route('/todo', methods=['PUT'])
def updateTodo():
    start_time = time.time()
    res = ''
    id = request.args.get('id')
    status = request.args.get('status')
    todo_logger.info('Update TODO id [' + str(id) + '] state to ' + status, extra={'request_number': request_counter})
    found = False

    if (status != 'PENDING' and status != 'LATE' and status != 'DONE'):  # check if the status is valid
        end_time = time.time()
        handle_request('/todo', 'PUT', end_time - start_time)  # log the request
        todo_logger.error('Error: Invalid input', extra={'request_number': request_counter})
        return jsonify({'errorMessage': 'Error: Invalid input'}), 400

    for todo in todos:
        if todo['id'] == int(id):
            oldStatus = todo['status']
            todo['status'] = status
            found = True
            break

    if found:
        todo_logger.debug('Todo id [' + str(id) + '] state change: ' + oldStatus + ' --> ' + status,
                          extra={'request_number': request_counter})
        end_time = time.time()
        handle_request('/todo', 'PUT', end_time - start_time)  # log the request
        return jsonify({'result': oldStatus}), 200
    else:
        todo_logger.error('Error: no such TODO with id ' + str(id), extra={'request_number': request_counter})
        end_time = time.time()
        handle_request('/todo', 'PUT', end_time - start_time)  # log the request
        return jsonify({'errorMessage': f'Error: no such TODO with id {id}”'}), 404


@app.route('/todo', methods=['DELETE'])
def deleteTodo():
    start_time = time.time()
    id = request.args.get('id')
    found = False

    for todo in todos:
        if (todo['id'] == int(id)):
            todos.remove(todo)
            found = True
            break

    end_time = time.time()
    if found:
        todo_logger.info('Removing todo id ' + str(id), extra={'request_number': request_counter})
        todo_logger.debug('After removing todo id [' + id + '] there are ' + str(len(todos)) + ' TODOs in the system',
                          extra={'request_number': request_counter})
        handle_request('/todo', 'DELETE', end_time - start_time)  # log the request
        return jsonify({'result': len(todos)}), 200

    else:
        todo_logger.error('Error: no such TODO with id ' + str(id), extra={'request_number': request_counter})
        handle_request('/todo', 'DELETE', end_time - start_time)  # log the request
        return jsonify({'errorMessage': f'Error: no such TODO with id {id}”'}), 404


@app.route('/logs/level', methods=['GET'])
def getLogLevel():
    start_time = time.time()
    logger_name = request.args.get('logger-name')

    if (logger_name == 'request-logger'):
        level = request_logger.getEffectiveLevel()
        level = logging.getLevelName(level)
        end_time = time.time()
        handle_request('/logs/level', 'GET', end_time - start_time)
        return str('result:' + str(level)), 200

    elif (logger_name == 'todo-logger'):
        level = todo_logger.getEffectiveLevel()
        level = logging.getLevelName(level)
        end_time = time.time()
        handle_request('/logs/level', 'GET', end_time - start_time)
        return str('result:' + str(level)), 200

    else:
        end_time = time.time()
        handle_request('/logs/level', 'GET', end_time - start_time)
        return str('errorMessage: Error: Invalid input'), 400


@app.route('/logs/level', methods=['PUT'])
def updateLogLevel():
    start_time = time.time()
    logger_name = request.args.get('logger-name')
    level = request.args.get('logger-level')

    if (logger_name != 'request-logger' and logger_name != 'todo-logger'):
        end_time = time.time()
        handle_request('/logs/level', 'PUT', end_time - start_time)
        return str('errorMessage: Error: Invalid input'), 400

    if (level != 'DEBUG' and level != 'INFO' and level != 'ERROR'):
        end_time = time.time()
        handle_request('/logs/level', 'PUT', end_time - start_time)
        return str('errorMessage: Error: Invalid input'), 400

    if (logger_name == 'request-logger'):
        request_logger.setLevel(level)

    elif (logger_name == 'todo-logger'):
        todo_logger.setLevel(level)

    end_time = time.time()
    handle_request('/logs/level', 'PUT', end_time - start_time)
    return str('result:' + (level)), 200
