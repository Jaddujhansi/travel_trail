from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import Optional
import google.generativeai as genai
import os
from pydantic import BaseModel
from dotenv import load_dotenv
import markdown

# Load environment variables
load_dotenv()

# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

genai.configure(api_key=GOOGLE_API_KEY)

# Initialize the model
model = genai.GenerativeModel('gemini-1.5-pro')

app = FastAPI()

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

class TravelPlan(BaseModel):
    destination: str
    start_date: str
    end_date: str
    interests: str
    budget: str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/create-plan", response_class=HTMLResponse)
async def create_plan(
    request: Request,
    destination: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    interests: str = Form(...),
    budget: str = Form(...)
):
    try:
        prompt = f"""
        Create a detailed travel plan for the following:
        Destination: {destination}
        Travel Dates: From {start_date} to {end_date}
        Interests: {interests}
        Budget: {budget}

        IMPORTANT: Format the response in a clear STEP-BY-STEP structure with proper headings and numbered steps.

        Please provide:

        ## DESTINATION OVERVIEW
        * Brief information about {destination} for travelers
        * Key facts travelers should know

        ## STEP-BY-STEP ITINERARY
        ### DAY 1: [Date]
        1. Morning: [Activities]
        2. Lunch: [Suggestions]
        3. Afternoon: [Activities]
        4. Dinner: [Suggestions]
        5. Evening: [Activities if applicable]

        [Continue for each day]

        ## TOP SIGHTSEEING SPOTS
        1. [Spot 1]: [Brief description]
        2. [Spot 2]: [Brief description]
        3. [Spot 3]: [Brief description]
        4. [Spot 4]: [Brief description]
        5. [Spot 5]: [Brief description]

        ## STEP-BY-STEP BUDGET BREAKDOWN (in Indian Rupees)
        * Convert all amounts to INR using 1 USD = 83 INR, 1 GBP = 105 INR, 1 EUR = 90 INR

        1. Accommodation
        2. Food
        3. Transportation
        4. Activities
        5. Miscellaneous
        6. Total

        ## STEP-BY-STEP TRAVEL TIPS
        1. Tip 1
        2. Tip 2
        3. Tip 3
        4. Tip 4
        5. Tip 5
        """

        response = model.generate_content(prompt)

        # Convert Markdown to HTML
        html_output = markdown.markdown(response.text, extensions=["fenced_code", "tables"])

        return templates.TemplateResponse("travel_plan.html", {
            "request": request,
            "destination": destination,
            "start_date": start_date,
            "end_date": end_date,
            "interests": interests,
            "budget": budget,
            "travel_plan": html_output
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update-plan", response_class=HTMLResponse)
async def update_plan(
    request: Request,
    current_plan: str = Form(...),
    update_request: str = Form(...)
):
    try:
        prompt = f"""
        Current travel plan:
        {current_plan}

        Request for update:
        {update_request}

        Please update the travel plan based on this request.
        Format using markdown with clear headings and bullet points.
        """

        response = model.generate_content(prompt)
        html_output = markdown.markdown(response.text, extensions=["fenced_code", "tables"])

        return templates.TemplateResponse("update_result.html", {
            "request": request,
            "updated_plan": html_output
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/explore-destination/{destination}", response_class=HTMLResponse)
async def explore_destination(request: Request, destination: str):
    try:
        prompt = f"""
        Provide detailed information about {destination} as a travel destination.

        Format:
        ## DESTINATION OVERVIEW
        * Brief history and background

        ## TOP ATTRACTIONS
        * Attraction: Description

        ## BEST TIME TO VISIT
        * Months, weather

        ## LOCAL CUISINE
        * Dishes and restaurant suggestions

        ## TRANSPORTATION OPTIONS
        * Local travel tips
        """

        response = model.generate_content(prompt)
        html_output = markdown.markdown(response.text, extensions=["fenced_code", "tables"])

        return templates.TemplateResponse("destination_info.html", {
            "request": request,
            "destination": destination,
            "info": html_output
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quick-ideas/{destination}/{interest}", response_class=HTMLResponse)
async def quick_ideas(request: Request, destination: str, interest: str):
    try:
        prompt = f"""
        Suggest 5 short activity ideas for someone interested in {interest} in {destination}.
        Format using markdown headers and bullet points.
        """

        response = model.generate_content(prompt)
        html_output = markdown.markdown(response.text, extensions=["fenced_code", "tables"])

        return templates.TemplateResponse("quick_ideas.html", {
            "request": request,
            "destination": destination,
            "interest": interest,
            "ideas": html_output
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
