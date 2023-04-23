from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import openai
from datetime import datetime

openai.api_key = "openai_api_key"

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    current_year = datetime.now().year
    return templates.TemplateResponse("index.html", {"request": request, "current_year": current_year})

@app.post("/get_horoscope", response_class=HTMLResponse)
async def get_horoscope(request: Request, astrology_sign: str = Form(...), area: str = Form(...), year_of_birth: int = Form(...)):
    horoscope = await get_horoscope_from_chatgpt(astrology_sign, year_of_birth, area)
    current_year = datetime.now().year
    return templates.TemplateResponse("index.html", {"request": request, "horoscope": horoscope, "current_year": current_year})


async def get_horoscope_from_chatgpt(astrology_sign: str, year_of_birth: int, area: str) -> str:
    today_date = datetime.now().strftime('%Y-%m-%d')
    prompt = [{"role": "system", "content": f"You are an expert astrologer and horoscope reader. You believe in astrology. "},
        {"role": "user", "content": f"Provide a daily horoscope reading based on the date today:{today_date} for {astrology_sign} born in {year_of_birth} for {area}."
                                          f"Mention the date  and day today as well. "
                                          f"Provide a lucky number and lucky color."
                                          f"The output should be in this format: 'Hi there {astrology_sign}! Your daily horoscope for [provide the date today] is as follows: [provide the horoscope]."
                                          f"Your lucky color is: [provide lucky color]"
                                          f"Your lucky number is: [provide lucky number]"
                                          f"Thank you!' "}]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.7,
        frequency_penalty=1,
        presence_penalty=0.1,
        messages=prompt,
        max_tokens=150,
        stream=False)

    horoscope = response.choices[0]['message']['content'].strip()
    return horoscope


