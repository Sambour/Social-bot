import openai
import os
from colorama import Fore, Style

openai.api_key = os.getenv("AZURE_OPENAI_KEY")
openai.api_version = "2024-02-15-preview" 
openai.api_type = "azure"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")

def chat(prompt:list):
    instruct = 'You are now a big movie fan chatting with a new friend about the movie area. You like reading books as well. You are enthusiastical and active, but don\'t provide make-up information. You should lead the conversation, and sometimes if the conditions are right, you can start a topic (movie or book) to discuss.'
    #sleep(60)
    msg = [{'role': 'system', 'content': instruct}]
    msg.extend(prompt)
    prediction = openai.ChatCompletion.create(
                    engine="AutoConcierge",
                    messages=msg,
                    max_tokens=300, temperature=1)
    output = prediction['choices'][0]['message']['content']
    return output

if __name__ == "__main__":
    input_str = ''
    prompt = []
    while input_str != 'quit':
        output = chat(prompt)
        print('\n' + Fore.YELLOW + 'Bot:' + Style.RESET_ALL)
        print(output + Fore.CYAN + '\n\nYou: ' + Style.RESET_ALL)
        prompt.append({'role': 'assistant', 'content': output})
        input_str = input()
        prompt.append({'role': 'user', 'content': input_str})
