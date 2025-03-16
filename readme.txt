# SmartMealPlanner

The Smart Meal Planner helps users manage their inventory of food items in their house. The app keeps track of every item in your kitchen and can help generate meal suggestions based on what items you have. Below, you will see how to download the app as well as the different functions and capabilities.

To install our app, you simply need to download SmartMealPlanner-client. In the Smart MealPlanner-client/docker folder, there is a separate readme with instructions on how to configure docker. Once, docker is running, type "python3 main.py" to run the application as intended.

Different commands:
0 - to exit the program
1 - this function will prompt the user to upload an image of a qr code containing text in the format of ITEMNAME-DD-MM-YY-QUANTITY. This program will add that item to the user's inventory, or update an existing item if the user already has som quantity of the item
2 - this function will show the user's inventory
3 - this function will allow the user to delete a certain quantity of a certain item in their inventory if they have consumed it
4 - this function will give the user an AI-generated meal plan for future meals based on the current inventory, prioritzing items that are going bad soon
5 - this function will allow the user to send in an email address and sends them an email with all items that are expiring within 3 days
