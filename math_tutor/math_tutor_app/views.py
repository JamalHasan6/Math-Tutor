from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from openai import OpenAI
from .event_handler import EventHandler  # can be used later once we implement streaming
import json

def home(request):
    if request.method == 'POST':
        if request.headers.get('Content-Type') == 'application/json':
            data = json.loads(request.body)
            user_input = data.get('user_input')
            conversation = request.session.get('conversation', [])

            if user_input:
                # Initialize OpenAI client
                client = OpenAI(api_key=settings.OPENAI_API_KEY)  # this uses Jamal's API key

                # Retrieve the assistant
                assistant = client.beta.assistants.retrieve('asst_ZEM9NLrHE8PHGosBQ3DxUFqH')

                # Create a new thread
                thread = client.beta.threads.create()

                conversation.append({"role": "user", "content": user_input})

                # Add a message to the thread (The user's message)
                message = client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=user_input
                )

                # Running the thread without streaming and event handling
                run = client.beta.threads.runs.create_and_poll(
                    thread_id=thread.id,
                    assistant_id=assistant.id,
                    instructions="Please address the user as Jamal. The user has a premium account."
                )

                if run.status == 'completed':
                    messages = client.beta.threads.messages.list(thread_id=thread.id)
                    chatbot_replies = messages.data[0].content[0].text.value

                    # Appending chatbot replies to the conversation
                    conversation.append({"role": "assistant", "content": chatbot_replies})
                else:
                    print(run.status)
                    chatbot_replies = "There was an error processing your request."

                # Update the conversation in the session
                request.session['conversation'] = conversation

                # Returning the reply as JSON
                return JsonResponse({'status': 'ok', 'reply': chatbot_replies})

        if 'clear_chat' in request.POST:
            # Clear the conversation
            request.session['conversation'] = []
            return redirect('home')  # Redirect to the home view after clearing

    conversation = request.session.get('conversation', [])

    # For GET requests, we have to render the page with the existing conversation
    return render(request, 'chat.html', {'conversation': conversation})
