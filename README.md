## What this bot was created for
This bot is designed to provide users with numbers. It can be used for giveaways or other purposes.

## What a bot can do
The user clicks on the "Get Number" button. Then the bot checks the database to see if the user has registered before, if not, it gives out a number, if yes, it writes "You have already registered".

Also, when sending the command /send_data bot sends Exel table, which contains all registered users, their number and telegram id.

## What you need to do for the bot to work
For the bot to work, you need to create a PostgreSQL table "user_data". In it you need to create 3 columns: user_id, fio, number.
