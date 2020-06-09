# party-room-bot-v4

GitHub Repo for Party Room Bot Version 4

Project Started - 9th April 2020



**Current Project Layout**

  **Cogs (each cog is used as a separate module for the bot)**
  
  	- Commands *rewritten* *partially complete*
	- Giveaways *rewritten* *complete*
	- Events(programming events not osrs based events) *new*
	- Tasks *new*
	- Games *rewritten* *partially complete*
      
  **Models (private classes and objects containing code the bot can access)**
  
  	- Bot (Custom bot model, overriding discord.commands.Bot) *new*
	- Config (model for json config file stored in the cloud allows for changes to bot without rebuilding an update) *new*
	- DBOperations (model for handling the database connections) *new*
	- Enums (Model containing Enumeration Classes for various parts of the bot)
	- Exceptions (Model containing custom exception classes for better error handling) *new*
	- Game (Model which all game objects inherit from. Contains several methods and variables) *new*
	- Giveaway (Reworked Giveaway Model for performance and cleaner code.) *rewritten*
	- RandomGame (Model for the Random Number Game) *new*
	- Utils (File containing several utility functions required by the bot) *new*
	
      
  **Major Changes**
  
  	- Changed Database Library from psycopg2 to asyncpg
	
  **To Be Added**
  
  	- Rest of v3.x to be rewritten
	- Add CrystalMathLabs API Usage
	- Command to check vanity roles and add them (staff only usage)
	- Cloud based settings file modification commands
	- Nitro Boosters Enter All giveaways
	- Auto assign roles based on join date (for steph): https://discordapp.com/channels/498848816976363531/635330099721273346/652400180565639179

