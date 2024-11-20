from flask import Flask, render_template, request, redirect, url_for, session
import openai
import os
from openai.error import OpenAIError, RateLimitError
from textblob import TextBlob
import json
import datetime

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

# Set up secret key for sessions
app.secret_key = 'your_secret_key_here'  # Make sure this key is kept private

# Path to JSON file to store user data
json_file_path = os.path.join(os.getcwd(), "game_user_data.json")

# Write an empty list to JSON if file does not exist
if not os.path.exists(json_file_path):
    with open(json_file_path, mode='w') as file:
        json.dump([], file)

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/home', methods=['POST'])
def home():
    first_name = request.form['first_name']
    last_initial = request.form['last_initial']
    grade_level = request.form['grade_level']
    start_time = datetime.datetime.now() 
    session['first_name'] = first_name
    session['last_initial'] = last_initial
    session['grade_level'] = grade_level
    session['start_time'] = start_time.strftime("%Y-%m-%d %H:%M:%S")
    session['session_key'] = f"{first_name}_{last_initial}_{start_time.timestamp()}"
    return render_template('home.html', first_name=first_name, last_initial=last_initial, grade_level=grade_level)

@app.route('/scenario/<scenario_id>', methods=['GET', 'POST'])
def scenario(scenario_id):
    scenario_data = {
        '1': {
            'title': "The Forest Path",
            'question': "You’re lost in the woods and must find your way back. What steps will you take to find your way back to safety?"
        },
        '2': {
            'title': "The Mystery of the Hidden Treasure",
            'question': "You’re on a treasure hunt and must solve clues to find the hidden treasure. How will you solve the mystery to uncover the treasure?"
        },
        '3': {
            'title': "Escape from the Wizard's Castle",
            'question': "You’re trapped in a castle with magical traps. Find a way to escape! What actions will you take to navigate the traps and escape?"
        }
    }

    scenario = scenario_data.get(scenario_id, {"title": "Invalid Scenario", "question": "Invalid scenario"})
    correct_answer = False  # Initialize correct_answer as False
    sentiment_text = ""
    response_text = ""

    if request.method == 'POST':
        player_response = request.form['response']
        try:
            # Use the Chat Completion API for gpt-3.5-turbo
            print("Calling OpenAI Chat API...")
            ai_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant guiding a player through an adventure."},
                    {"role": "user", "content": f"Scenario: {scenario['question']}"},
                    {"role": "user", "content": f"Player's Response: {player_response}"}
                ],
                max_tokens=150
            )
            response_text = ai_response['choices'][0]['message']['content'].strip()
            print(f"API Response: {response_text}")

            # Simple Sentiment Analysis with TextBlob
            sentiment = TextBlob(player_response).sentiment.polarity
            if sentiment > 0:
                sentiment_text = "Positive sentiment detected in your response!"
                correct_answer = True  # Set correct_answer to True if sentiment is positive
            elif sentiment < 0:
                sentiment_text = "Negative sentiment detected in your response."
            else:
                sentiment_text = "Neutral sentiment detected in your response."

        except RateLimitError:
            response_text = "Sorry, the system is currently busy. Please try again later."
            print("Rate limit exceeded")
        except OpenAIError as e:
            response_text = f"An error occurred: {str(e)}"
            print(f"OpenAI error: {e}")
        except Exception as e:
            response_text = "An unexpected error occurred."
            print(f"Unexpected error: {e}")

        return render_template('scenario.html', title=scenario['title'], question=scenario['question'], ai_response=response_text, sentiment=sentiment_text, correct_answer=correct_answer)
    
    return render_template('scenario.html', title=scenario['title'], question=scenario['question'])

@app.route('/ending', methods=['GET'])
def ending():
    # Retrieve the user's session information
    first_name = session.get('first_name')
    last_initial = session.get('last_initial')
    grade_level = session.get('grade_level')
    start_time_str = session.get('start_time')
    end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Get the start time from the session and write the session data to JSON
    if first_name and last_initial and start_time_str:
        user_data = {
            "First Name": first_name,
            "Last Initial": last_initial,
            "Grade Level": grade_level,
            "Start Time": start_time_str,
            "End Time": end_time
        }
        
        # Append the new data to the existing JSON file
        with open(json_file_path, mode='r+') as file:
            data = json.load(file)
            data.append(user_data)
            file.seek(0)
            json.dump(data, file, indent=4)

    return render_template('ending.html')

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))  # Default to port 5000 if PORT is not set
    app.run(host='0.0.0.0', port=port, debug=True)

