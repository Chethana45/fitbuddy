import os
import google.generativeai as genai
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

if API_KEY and API_KEY != "YOUR_API_KEY_HERE":
    genai.configure(api_key=API_KEY)
    # Switched to gemini-2.5-flash because gemini-1.5-flash is not available and 2.0-flash-lite quota was exceeded
    system_instruction = "You are an expert fitness coach. ALWAYS respond with plain, complete Markdown text."
    model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=system_instruction)
else:
    model = None

def generate_workout_plan(name: str, age: int, gender: str, weight: int, goal: str, intensity: str) -> str:
    if not model:
        return "Error: Google Gemini API key is not configured."
    
    prompt = f"""
    You are an expert fitness coach and AI requested to generate a customized 7-day workout plan.
    User Profile:
    - Name: {name}
    - Age: {age}
    - Gender: {gender}
    - Weight: {weight} kg
    - Primary Goal: {goal}
    - Preferred Workout Intensity: {intensity}

    Please provide a structured, day-by-day 7-day workout plan tailored to this user's profile.
    Include specific exercises, sets, and reps where applicable.
    Format your response in plain Markdown. Do not use code blocks for the entire response, just regular markdown lists and headers.
    Keep the tone motivating and professional.
    """
    
    try:
        response = model.generate_content(prompt)
        # Check if the response contains any text before accessing it
        if response.parts:
            return response.text
        else:
            return f"Failed to generate workout plan: No text returned. (Finish reason: {response.candidates[0].finish_reason if response.candidates else 'Unknown'})"
    except Exception as e:
        return f"Failed to generate workout plan: {e}"

def revise_workout_plan(current_plan: str, feedback: str) -> str:
    if not model:
        return "Error: Google Gemini API key is not configured."
    
    prompt = f"""
    You are an expert fitness coach. Below is a 7-day workout plan currently prescribed to a user:
    
    ---
    {current_plan}
    ---
    
    The user has provided the following feedback to adjust the plan:
    "{feedback}"
    
    Please revise the 7-day workout plan to incorporate the user's feedback. Maintain the aspects that the user didn't mention changing, but adapt according to their new desires.
    Format your response in plain Markdown. Keep the tone motivating.
    """
    
    try:
        response = model.generate_content(prompt)
        if response.parts:
            return response.text
        else:
            return f"Failed to revise workout plan: No text returned. (Finish reason: {response.candidates[0].finish_reason if response.candidates else 'Unknown'})"
    except Exception as e:
        return f"Failed to revise workout plan: {e}"

def generate_nutrition_tip(goal: str) -> str:
    if not model:
        return "Error: API key not configured."
    
    prompt = f"""
    You are a nutrition and recovery expert. Provide a single, concise (1-2 sentences) and actionable nutrition or recovery tip 
    tailored specifically for a fitness goal of: "{goal}".
    Do not add extra conversational text, just the tip itself.
    """
    
    try:
        response = model.generate_content(prompt)
        if response.parts:
            return response.text.strip()
        else:
            return f"Failed to generate tip: No text returned."
    except Exception as e:
        return f"Failed to generate tip: {e}"
