from flask import Flask, render_template, request
from flask_socketio import SocketIO
import json
import random

app = Flask(__name__)
socketio = SocketIO(app)
next_counter = 0
question_counter = 0
player_results = {}
player_names = {}
name_list = []
questions = []

def generate_questions():
    global questions
    with open("dataset.json", "r") as file:
        questions = json.load(file)
    random.shuffle(questions)
    questions = questions[:min(len(questions), 10)]

def reset_data():
    global next_counter, question_counter, player_results, player_names
    next_counter = 0
    question_counter = 0
    player_results = {}
    player_names = {}
    generate_questions()

@socketio.on('connect')
def handle_connect():
    global player_results
    if request.sid not in player_results.keys():
        player_results[request.sid] = 0

@socketio.on('disconnect')
def handle_disconnect():
    global next_counter, question_counter, player_results, player_names
    if request.sid in player_results.keys():
        del player_results[request.sid]
        if request.sid in player_names.keys():
            del player_names[request.sid]
    if len(player_results) == 0:
        reset_data()

@socketio.on('send_next')
def handle_button_click(data):
    global next_counter, question_counter, player_results, player_names, questions, name_list
    if request.sid not in player_names.keys():
        player_names[request.sid] = data["name"]
    if (data["answer"] == questions[question_counter][1]):
        player_results[request.sid] += 1
    next_counter += 1
    if next_counter >= len(player_results):
        next_counter = 0
        question_counter += 1
        if question_counter >= len(questions):
            name_list = [f"{name} - {value}" for name, value in sorted(zip(player_names.values(), player_results.values()), key=lambda item: item[1], reverse=True)]
            reset_data()
            socketio.emit('load_page', {'url': '/leaderboard'})
        else:
            socketio.emit('got_next', {"sentence": questions[question_counter][0]})

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/quiz')
def quiz():
    global question_counter, questions
    return render_template('quiz.html', question=questions[question_counter][0])

@app.route('/leaderboard')
def leaderboard():
    global name_list
    return render_template('leaderboard.html', names=name_list)

if __name__ == '__main__':
    generate_questions()
    app.run("127.0.0.1", 80)