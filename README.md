# ReminderBot

<img src="https://travis-ci.org/ytturi/reminder_bot.svg?branch=master" alt="build:">


## Usage

This bot is intended to facilitate event reminders within a group.

Once the bot is enabled within a group it will start storing events for it.

### Register an event

You can register (and update) an event by running:

```
/register <date>|<title>|<description>
```

The date is a datetime and must be in the format: `dd-mm-yyyy HH:MM`

### List current events

You can use the shortcuts for `/next` and `/last` events.
Or you can use the `/list` command.

You can list an specific amount of events `/list <amount>`.    
You can also filter on only past or future events `/list past`

And of course you can list all the events with `/list all` and combine it with `past`/`next`

Listing events also shows their ID

### Show an event

With the ID of an event you can show the description with `/event <eventId>`.

This could allow, for instance, to update the description after the event has ocurred and you can show a briefing of the session to the group.

### Pin next event

With `/pin` you can instantly show the next event and pin the message.