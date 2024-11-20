from flask import Flask, render_template, request, redirect, url_for
import openai
import os
from openai.error import OpenAIError, RateLimitError
from textblob import TextBlob

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/home', methods=['POST'])
def home():
    first_name = request.form['first_name']
    last_initial = request.form['last_initial']
    grade_level = request.form['grade_level']
    return render_template('home.html', first_name=first_name)

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
    return render_template('ending.html')

if __name__ == '__main__':
    app.run(debug=True)