

from openai import OpenAI
from typing_extensions import override
from openai import AssistantEventHandler

client = OpenAI(api_key="sk-proj-tte2SNxtWikZyhEkCvb2T3BlbkFJaDkUp9iYRhUcMpdqu5XT")  # this uses Jamal's API key




# # Upload a file with an "assistants" purpose
# course_outline_file = client.files.create(
#   file=open("MATH1120-2024-S1-CALLAGHAN.pdf", "rb"),
#   purpose='assistants'
# )

# instructions = '''You are an experienced Mathematics tutor, helping students with the course MATH1120. 
# You use code interpreter when solving mathematics problems and you have access to the course outline to answer questions about the course itself.
# Your text outputs should be valid html with LaTeX, not markdown.
# '''

# # Add the file to the assistant
# assistant = client.beta.assistants.create(
#   instructions=instructions,
#   model="gpt-4-turbo-2024-04-09",
#   tools=[
#       {"type": "retrieval"},
#       {"type": "code_interpreter"}
#   ],
#   file_ids=[course_outline_file.id]
# )


# We can create a new assistant by uncommenting the above, but it's cleaner to use an existing one:
assistant = client.beta.assistants.retrieve('asst_ZEM9NLrHE8PHGosBQ3DxUFqH')

# assistant = client.beta.assistants.create(
#   name="Math Tutor",
#   instructions="You are a personal math tutor. Write and run code to answer math questions.",
#   tools=[{"type": "code_interpreter"}],
#   model="gpt-4-turbo-preview",
# )


import ipywidgets as w


output = w.Output(layout={'max_height' : '1000px', 
                          'overflow_y' : 'auto'})

text_widget_list = []   # the textr outputs are lsited here, will be displayed in output
image_widget_list = [] 
tool_widget_list = []

user_input = w.Textarea(placeholder='Type something and click send',
                        layout={'width': '70%'})
send_button = w.Button(icon='paper-plane', 
                       description='Send',
                       layout={'width': '80px',
                               'height': '60px'
                              })

thread = client.beta.threads.create()


def create_user_message(text='', icon='user'):
    '''Return HTMLMath widget'''
    global text_widget_list
    html = f'<i class="fa fa-{icon}" aria-hidden="true"></i> ' + text
    widget = w.HTMLMath(value=html, layout={'border' : '1px solid yellow'})
    text_widget_list.append(widget)
    with output:
        display(widget)
    return widget
    

def create_new_text_output(text='', icon='robot'):
    '''Return an HTMLMath widget'''
    global text_widget_list
    html = f'<i class="fa fa-{icon}" aria-hidden="true"></i> ' + text
    widget = w.HTMLMath(value=html, layout={'border' : '1px solid blue'})
    text_widget_list.append(widget)
    with output:
        display(widget)
    return widget

def update_text_output(text, widget=None):
    if widget is None:  # default is the most recent widget in the list
        widget = text_widget_list[-1]
    widget.value += text.replace('\n','<br>')

def create_new_tool_widget(text='', icon='cogs'):
    '''Return HTML widget'''
    global tool_widget_list
    template = f'''
<style>
.code-block {{
    font-family: "Courier New", Courier, monospace; /* Monospace font */
    background-color: #f9f9f9; /* Light gray background */
    color: #333; /* Dark text color for readability */
    padding: 10px; /* Padding inside the code block */
    margin: 10px 0; /* Margin around the code block */
    border: 1px solid #ccc; /* Light gray border */
    border-radius: 5px; /* Slightly rounded corners */
    overflow-x: auto; /* Horizontal scrolling for long lines */
    white-space: pre; /* Maintains whitespace (like indentations) */
}}
</style>
<i class="fa fa-{icon}" aria-hidden="true"></i> <b>{text}</b><br>
<pre class="code-block">
[CONTENT]
</pre>
'''
    # html = f'<i class="fa fa-{icon}" aria-hidden="true"></i> <b>{text}</b><br>'
    widget = w.HTML(layout={'border' : '1px solid red'})
    widget.template = template
    widget.content = ''
    widget.value = widget.template.replace('[CONTENT]', '')
    tool_widget_list.append(widget)
    with output:
        display(widget)
    return widget

def update_tool_widget(text, widget=None):
    if widget is None:  # default is the most recent widget in the list
        widget = tool_widget_list[-1]
    widget.content += text
    widget.value = widget.template.replace('[CONTENT]', widget.content)
    # widget.value += text.replace('\n','<br>')

def create_image_widget(img):
    '''return Image widget'''
    global image_widget_list
    widget = w.Image(value=img)
    image_widget_list.append(widget)
    with output:
        display(widget)
    return widget



class EventHandler_w(AssistantEventHandler):    
    @override
    def on_text_created(self, text) -> None:
        create_new_text_output()
        # with output:
        #     print(f'Text created: {text}')
      
    @override
    def on_text_delta(self, delta, snapshot):
        update_text_output(str(delta.value))

    @override
    def on_text_done(self, text):
        with output:
            for item in text.annotations:
                print(item)
            # print(f'Text done:\n {text} ')

    @override
    def on_image_file_done(self, image_file):  
        with output:
            print(f'Image received: {image_file.file_id}')
            image_data = client.files.content(image_file.file_id)
            image_data_bytes = image_data.read()
            create_image_widget(image_data_bytes)
            # display(w.Image(value=image_data_bytes))
      
    def on_tool_call_created(self, tool_call):
        create_new_tool_widget(str(tool_call.type))
  
    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == 'code_interpreter':
            if delta.code_interpreter.input:
                update_tool_widget(str(delta.code_interpreter.input))
                # print(delta.code_interpreter.input, end="", flush=True)
            if delta.code_interpreter.outputs:
                update_tool_widget('<br><b>Output:</b><br>')
                # print(f"\n\noutput >", flush=True)
                for item in delta.code_interpreter.outputs:
                    if item.type == "logs":
                        update_tool_widget(f'<br>{item.logs}')
                    else:
                        with output:
                            print(f'Code Interpreter output of type {item.type}:\n{item}')
        else:
            with output:
                print(f'Tool call delta of type: {delta.type}:\n{delta}')

    def on_tool_call_done(self, tool_call):
        with output:
            print(f' Tool call completed:\n{tool_call}')

    def on_exception(self, exception):
        with output:
            print(f'*** {exception} ')

   

def run_query(b):
    '''User has clicked "send". Run assistant.'''
    print('dkjfgg')
    text = user_input.value
    if len(text) == 0:
        return
    create_user_message(text)
    send_button.disabled = True
    
    # run assistant with streaming
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=text
    )
    
    with client.beta.threads.runs.stream(
        thread_id=thread.id,
        assistant_id=assistant.id,
        instructions="Please produce html output in your response text. You may also use valid LaTeX.",
        event_handler=EventHandler_w(),    # needs a fresh event_handler each time...
    ) as stream:
        stream.until_done()
        
    send_button.disabled = False
    user_input.value=''

send_button.on_click(run_query)


output.clear_output()
display(output)
display(w.HBox([user_input, send_button]))