from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import openai
import os
import io
import nltk
from nltk.tokenize import sent_tokenize
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

openai.api_key = os.getenv('OPENAI_API_KEY')

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    current_year = datetime.now().year
    return templates.TemplateResponse("index.html", {"request": request, "current_year": current_year})

@app.post("/get_horoscope", response_class=StreamingResponse)
async def get_horoscope(request: Request, astrology_sign: str = Form(...), area: str = Form(...), name: str = Form(...)):
    horoscope = await get_horoscope_from_chatgpt(astrology_sign, name, area)
    #current_year = datetime.now().year
    image_bytes = await create_horoscope_image(horoscope)
    return StreamingResponse(io.BytesIO(image_bytes), media_type="image/png")

async def get_horoscope_from_chatgpt(astrology_sign: str, name: str, area: str) -> str:
    today_date = datetime.now().strftime('%Y-%m-%d')
    current_day = datetime.now().strftime('%A')
    prompt = [{"role": "system", "content": f"You are an expert astrologer and horoscope reader. You believe in astrology. "},
        {"role": "user", "content": f"Provide a daily horoscope reading based on the date today:{today_date}, {current_day} for {astrology_sign} for {area}."
                                          f"Mention the date  and day today as well. "
                                          f"The output should have separate sentences in this format: 'Hi there {name}! Here's your daily horoscope for {astrology_sign}, [provide the date today, {today_date} and current day, {current_day}]. [provide the horoscope]."
                                        f"Try to make it funny and witty "
                                    f"Strictly keep it under 4 sentences."
                                          }]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.5,
        frequency_penalty=1.4,
        presence_penalty=0.1,
        messages=prompt,
        max_tokens=80,
        stream=False)

    horoscope = response.choices[0]['message']['content'].strip()
    return horoscope

def split_sentences(text):
    sentences = sent_tokenize(text)
    return [sentence.strip() for sentence in sentences if sentence.strip()]


# Updated create_horoscope_image function
async def create_horoscope_image(horoscope: str) -> bytes:
    # Create a blank image with a white background and increased dimensions
    width, height = 600, 400
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)

    # Load a font and set its size
    font = ImageFont.truetype("static/fonts/Muli.ttf", 20)

    # Split the horoscope text into sentences
    sentences = split_sentences(horoscope)

    # Calculate the initial Y position
    y_text = height // 6
    max_width = width - 40  # Leave some padding on both sides of the image
    for sentence in sentences:
        wrapped_text = wrap_text(sentence, font, max_width)

        for line in wrapped_text:
            # Calculate the X position to center the text
            line_width, line_height = font.getsize(line)
            x_text = (width - line_width) // 2
            draw.text((x_text, y_text), line, font=font, fill='black')
            y_text += line_height

    # Save the image in memory as a PNG
    image_bytes = io.BytesIO()
    image.save(image_bytes, "PNG")
    image_bytes.seek(0)
    return image_bytes.getvalue()


def wrap_text(text, font, max_width):
    sentences = sent_tokenize(text)
    lines = []

    for sentence in sentences:
        words = sentence.split()

        line_width, _ = font.getsize(sentence)

        # If the sentence is too long, find a break point near the middle
        if line_width > max_width:
            middle = len(words) // 2
            break_point = middle

            # Iterate until we find a suitable break point
            while break_point > 0 and font.getsize(' '.join(words[:break_point]))[0] > max_width:
                break_point -= 1

            # If we found a break point, split the sentence
            if break_point > 0:
                line1 = ' '.join(words[:break_point])
                line2 = ' '.join(words[break_point:])
                lines.extend([line1, line2])
            else:
                lines.append(sentence)
        else:
            lines.append(sentence)

    return lines
