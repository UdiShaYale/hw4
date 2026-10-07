Problem #2: Analyze the database

We're building a website for 'Campus Customs'.  look at the campus_customs.db file and help me understand the fields of the table. write the table and its fields and one short line on why each field matters in output/harness.md file.


Problem #3:  Build the Campus Customs wesbite

Now we are going to build a website. create a React+Vite+TypeScript front end for Campus Customs. Add a nav bar at the top for Home, Products, About Us, Log In, Create Account. 
For the Home page, add the Yale logo. in the About Us page, give a brief history of the university and the merch company.
For the Products page, show the images of the products from the catalogue(use the image paths in the database) along with basic product information (name, price, description)
Make each product open a single-item page (large image on one side, full product text on the other - description, price, sizes/ stock when you have them). clicking on a card on products should take the shopper there.
Add a chat interface at the bottom right that will call the backend.
Create a FastAPI app in backend/main.py to read the database


Problem #4: Create account and login

Now we build the create-account/ login flow. for create account, we need first name, last name, email, password (confirm password); Log in: email and password.
New accounts will be added to the users table. store passwords securely do hackers cannot access them.
Update the output/harness.md with how the auth works (what you stored for users and how passwords are protected)


Problem #5: PydanticAI agent backend

For the chatbot, create a PydanticAi agent behind a FastAPI plugged into the chat widget. put the api app in backend/main.py and run the file with Uvicorn. These are the agent files:
backend/prompts/prompt.md
backend/agent.py
backend/tools.py
backend/models.py

In main.py, expose a chat route so that a message from the website returns a reply from the agent. use the api key in .env file.
Put campus customs voice and safety basics into prompts/prompt.md. start and update the types in models.py for chat replies and product cards as needed.
In output/harness.md, note how the front end talks to the FastAPI and how the agent is loaded. Backend should run from: uvicorn main:app --reload --port 8000

Problem #6: Tools - product info and stock

The agent should be able to use tools (product description, price, how many are in stock) to look up real information from campus_customs.db
Agent must use the database DO NOT INVENT PRICES OR QUANTITIES. If a size is out of stock, say so. expand prompts/prompt.md so the agent knows to call these tools for price and stock questions. add or update return types in models.py
In output/harness.md, list each tool and explain which model fields you chose to lookup and why.

Problem #7: Chat search that updates the page

When a customer asks about a type of item, the agent should search the catalogue and the website should dynamically show the matching items as product cards (image, name, price, short description). this is an api, the agent returns structured product matches and then the frontend renders them on the website.
Once the dynamic product cards are loaded, ensure the single-item page behavior works. update prompts/prompt.md and output/harness.md

Problem #8: Customer memory

when a shopper is logged in, save the chat history in the database in an appropriate table and reload when they return. the agent should know who is chatting (add that in agent dependencies and a tool the agent can call).
Also, pass enough context so that the agent knows which item the user is asking about on a product page. this can be put into the agent context as code.
History only persists for logged-in users. Document in output/harness.md how the chat history is stored, what customer fields the agent can see and how page context is passed.

Problem #9: Usability improvements

I noticed the spelling of 'colour' is wrong in the search bar. Fix that error. Also, the last name textbox under Create Account is spilling over.
What are 2 front-end and back-end improvements we can make? Create output/usability.md while building the enhancements. Say what you added and how it helped a shopper or the business.


Problem #10: Style the website

Change the font style for the headers on the nav bar compared to the content on the page.
Also, for each product card, increase the font size of the category and make it a different color. 
Update the About Us page to have text content in right side bar. 
Write output/design.md with what you changed and why customers would stay and buy

Problem #11: 

Create output/app_check.html. Include screenshots and captions for:
1. Chat checking the inventory of an item
2. Dynamic search-result cards
3. Sort control on Products
Put the screenshots in output/app_check_images/ and link them from app_check.html with relevants paths


Problem #12: Audit trail, safety, finish harness

Keep an apend-only output/audit_trail.json of agent loop activity (time, tool name, short args/result, stop reason). Do not wipe between runs. Think of safety rules to give the agent in prompts/prompt.md
Finish output/harness.md. Model fields in models.py and why you chose them, tools and abilities, safety rules, specs(loop limit, result caps, models)