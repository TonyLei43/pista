from flask import Flask, request
import requests
from index import setup
from twilio.twiml.messaging_response import MessagingResponse
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Access the environment variables
openai_api_key = os.getenv('OPENAI_API_KEY')
twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_number = os.getenv('TWILIO_NUMBER')

app = Flask(__name__)

@app.route('/sms', methods=['POST', 'GET'])
def sms_reply():
    incoming_msg = request.form['Body']
    from_number = request.form['From']
    myCassandraVStore, llm = setup()
    # Process the message and get a response
    response = process_message(incoming_msg, myCassandraVStore, llm)

    resp = MessagingResponse()
    msg = resp.message()
    msg.body(response)

    # Send the response back to the user
    send_sms(response, from_number)

    return '', 200

def process_message(message, myCassandraVStore, llm):
    response = query_custom_gpt(message, myCassandraVStore, llm)
    return response

def send_sms(response, to_number):
    url = f'https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}/Messages.json'
    
    data = {
        'From': twilio_number,
        'To': to_number,
        'Body': response
    }

    requests.post(url, data=data, auth=(twilio_account_sid, twilio_auth_token))

def query_custom_gpt(message, myCassandraVStore, llm):
    retrieved_docs = myCassandraVStore.similarity_search_with_score(message, k=4)
    context = "\n\n".join([f"{doc.page_content[:]}" for doc, _ in retrieved_docs])  # Limit context length if necessary
    instructions = (
        "You are a good chatbot assisting the customer and you speak like you are on our behalf. "
        "If there is no data for the question, please look it up on the internet. If it is something that you can't answer, respond with 'I would refer you to our cashiers'. Limit your responses to a short text message approximately at a maximum with 100-150 words."
    )

    # Generate response using the context, the query, and the instructions
    full_prompt = f"Instructions: {instructions}\n\nContext: {context}\n\nQuestion: {message}\n\n"
    llm_result = llm.generate([full_prompt])
    answer = llm_result.generations[0][0].text.strip()

    print(f"Answer: {answer}")
    return answer

if __name__ == '__main__':
    app.run(debug=True, port=8080)
