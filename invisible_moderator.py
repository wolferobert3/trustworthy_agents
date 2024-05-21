import openai
import gradio as gr
import requests
import os

from openai import OpenAI
from PIL import Image
from datetime import datetime

openai.api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI()

BLOCKED_IMAGE = 'blocked.png'
DEFAULT_IMAGE = 'default.png'
LOG_FILE = 'log.txt'
IMG_DIR = 'images'

if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)

def generate_from_dalle(prompt: str, secret: str):
    """
    Generate an image from DALL-E 3 based on a user-specified prompt and download the image.
    """
    
    # Combine the prompt and secret
    input = f'{prompt} {secret}'
    img_name = str(len([i for i in os.listdir(IMG_DIR) if i.endswith('.png')]) + 1)
    time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Check the prompt for any violence, hate speech, or sexual content
    check = review_prompt_gpt4(input)

    # If the prompt contains any violence, hate speech, or sexual content, return the blocked image
    if check.lower().strip().replace('\'','').replace('\"','') != 'no':

        image = Image.open(BLOCKED_IMAGE)
        image.save(f"{IMG_DIR}/{img_name}.png")

        with open(LOG_FILE, 'a') as f:
            f.write(f"Time - {time}\n")
            f.write(f"Image {img_name} : Prompt - {prompt} - Secret - {secret} - BLOCKED\n")

        return image

    # Generate the image from DALL-E 3
    response = client.images.generate(
      model="dall-e-3",
      prompt=input,
      size="1024x1024",
      quality="standard",
      n=1,
    )
    
    # Get the image URL
    image_url = response.data[0].url

    # Download and save the image
    image = Image.open(requests.get(image_url, stream=True).raw)
    image.save(f"{IMG_DIR}/{img_name}.png")

    with open(LOG_FILE, 'a') as f:
        f.write(f"Time - {time}\n")
        f.write(f"Image {img_name} : Prompt - {prompt} - Secret - {secret} - ALLOWED\n")

    return image

def review_prompt_gpt4(prompt: str):
    """
    Review a prompt to determine if it contains any violence, hate speech, or sexual content.
    """

    input = f'Please determine if the following DALL-E 3 prompt contains any violence, hate speech, or sexual content and output only yes or no. Prompt {prompt}. Your determination (yes or no):'

    response = client.chat.completions.create(
    model="gpt-4-turbo-preview",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": input},
    ]
    )

    return response.choices[0].message.content

with gr.Blocks() as interface:

    gr.Markdown("# Image Creator")

    with gr.Row():

        with gr.Column():

            prompt = gr.Textbox(label="What image should be created?", placeholder="Describe the picture you want to be created.")
            button = gr.Button("Generate Image")
            
            with gr.Accordion("Rule for Fair AI", open=False):
                secret = gr.Textbox(label="Rule", placeholder="Enter the rule to create fair AI here.")

        with gr.Column():

            with gr.Row():

                image_output = gr.Image(label="Make an Image", value=DEFAULT_IMAGE, type="pil")
    
    button.click(generate_from_dalle, inputs=[prompt, secret], outputs=[image_output])

interface.launch(share=True)