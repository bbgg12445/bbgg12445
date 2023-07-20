from flask import Flask, render_template, request
import openai
import pandas as pd

app = Flask(__name__)

# Replace 'YOUR_OPENAI_API_KEY' with your actual OpenAI API key
openai.api_key = "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"

# Initialize total score as integer
irange = 5

class ChatBot:
    def __init__(self, text_document):
        self.text_document = text_document
        self.score_df = pd.DataFrame(columns=['Question', 'User Response', 'Score'])
        self.current_question_index = 0

    def generate_next_question(self):
        # Use the AI model to generate the next question from the text document
        question_prompt = self.text_document[self.current_question_index:self.current_question_index+2000]
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo-16k", messages=[
            {"role": "system", "content": "You are a finance and accounting trainer. Your job is to generate a question and a sample answer based on the text provided to you. Ask a short and simple question that the trainee can answer in a concise manner."},
            {"role": "user", "content": question_prompt},
        ])
        self.current_question_index += 2000
        print(response['choices'][0]['message']['content'])
        return response['choices'][0]['message']['content']

    def get_user_response(self, question):
        # Get the user's response to a question
        print(question)
        user_response = input("Your answer: ")
        return user_response

    def score_response(self, question, user_response):
        # Score the user's response by comparing it with the AI model's answer
        scoring_prompt = f"{question}\nAI's answer: {self.text_document[:100]}\nUser's answer: {user_response}"
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo-16k", messages=[
        {"role": "system", "content": "You are a finance and accounting trainer. your job is to score the trainees answer based on the question and the sample answer provided to you. Rate the user's response on a scale of 1 to 10, with 10 being the most accurate. ONLY GIVE A single number in your respnse."},
        {"role": "user", "content": scoring_prompt},
        ])
        score = response['choices'][0]['message']['content']
        print (score)
        return int(score)

    @staticmethod
    def calculate_total_score(score_df):
        # Calculate the total score of the user's responses
        return score_df['Score'].sum()

    @staticmethod
    def determine_pass_fail(total_score):
        total_score = int(total_score)
        # Determine whether the user passed or failed based on the total score
        return "passed" if total_score >= irange*5 else "failed"

# Initialize chatbot instance outside the view function
with open("text_document.txt", "r") as file:
    text_document = file.read()
chatbot = ChatBot(text_document)

@app.route('/', methods=['GET', 'POST'])
def index():
    global chatbot

    if request.method == 'POST':
        user_response = request.form['user_response']
        question = chatbot.generate_next_question()
        score = chatbot.score_response(question, user_response)
        chatbot.score_df = chatbot.score_df._append({'Question': question, 'User Response': user_response, 'Score': score}, ignore_index=True)

        if chatbot.current_question_index >= len(chatbot.text_document) or chatbot.current_question_index == irange * 2000:
            total_score = chatbot.calculate_total_score(score_df=chatbot.score_df)
            pass_fail = chatbot.determine_pass_fail(total_score)
            return render_template('quiz.html', total_score=total_score, pass_fail=pass_fail, score_df=chatbot.score_df)
        else:
            return render_template('index.html', question=question)

    else:
        question = chatbot.generate_next_question()
        return render_template('index.html', question=question)

@app.route('/reset', methods=['GET'])
def reset_quiz():
    global chatbot
    chatbot = ChatBot(chatbot.text_document)
    question = chatbot.generate_next_question()
    return render_template('index.html', question=question)

if __name__ == "__main__":
    app.run(debug=True)
