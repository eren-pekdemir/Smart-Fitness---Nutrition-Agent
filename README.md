Step 1 – Project Progress Journal (24.04.2026)
1. Short description of the planned system and its goal
My project is a Smart Fitness and Diet Assistant. Since I personally spend a lot of time at the gym and track my macros, I want to make this process easier. The goal is to create an AI agent where the user can just type something like "I had a protein shake and 2 bananas," and the system will automatically find the calories/macros and log them. Instead of searching a database manually, the AI will handle the "finding and calculating" part.

2. Description of the AI or agent-based approach
I will build a single intelligent agent using Python. The agent will act as a "brain." When a user sends a message, the AI will analyze the text to understand the intent. If it's about food, it will call a nutrition tool. If the user asks about their progress, it will look at the database. I plan to use the ReAct (Reasoning and Acting) logic so the agent can decide which step to take next depending on the user's input.

3. List of tools that will be used in the system
To make the system work, I will create at least three main tools:

NutritionLookupTool: This tool will connect to a web API (like Edamam or Nutritionix) to get real-time data about food (calories, protein, fats).

BodyCalcTool: A local Python tool that calculates the user's BMR (Basal Metabolic Rate) and daily needs using basic math formulas.

StorageTool: A simple module to save and read data from a local file (like a CSV or a small SQLite database) so the user can see their history.

4. Preliminary list of programming concepts required
For this project, I will need to use these concepts:

OOP (Classes): To keep my code organized by creating classes for the Agent and the Tools.

API Requests: I need to use the requests library to get data from the internet.

Data Handling: Working with JSON data (since APIs usually send JSON) and converting it into Python dictionaries.

Error Handling: Using try-except blocks so the program doesn't crash if the API is down or the user types something weird.

Environment Variables: Keeping my API keys safe in a .env file.