import discord
import os
from dotenv import load_dotenv
from tinydb import TinyDB, Query

load_dotenv()
client = discord.Client()
db = TinyDB('db.json')
q = Query()


def add_item(groceries, entry_id, name, item):
	groceries.append(item)

	# update list in db
	db.update({'grocery_list': groceries}, doc_ids=[entry_id])

	return name + " added [" + item + "] to the list.\n"


def edit_item(groceries, entry_id, name, index, new_name):

	if (not index.isnumeric() and int(index)-1 >= len(groceries)):
		return index + " is not a valid index.\n"
	item = groceries[int(index)-1]
	groceries[int(index)-1] = new_name

	# update list in db
	db.update({'grocery_list': groceries}, doc_ids=[entry_id])

	return name + " changed [" + item + "] to [" + new_name + "].\n"


def del_item(groceries, entry_id, name, indices):

	delIndices = []
	msg = ''

	for index in indices:

		# skip if index is not an integer or if index out of bounds
		if (not index.isnumeric() or int(index)-1 >= len(groceries) or int(index)-1 < 0):
			msg += index + " is not a valid index.\n"
			continue

		# set each deletion index to ''
		item_index = int(index)-1
		delIndices.append(item_index)
		msg += name + " deleted [" + groceries[item_index] + "] from the list.\n"

	# add items which are not in delIndices
	updated_groceries = []
	for i in range(len(groceries)):
		if i not in delIndices:
			updated_groceries.append(groceries[i])
	groceries = updated_groceries

	# update list in db
	db.update({'grocery_list': groceries}, doc_ids=[entry_id])

	return msg


# uses del_item() to delete all other indices
def keep_item(groceries, entry_id, name, indices):

	keep_indices = []
	new_indices = []
	
	# cast all indices to int
	for x in indices:
		if x.isnumeric():
			keep_indices.append(int(x))

	# del indices that are not in 
	for i in range(len(groceries)):
		if i+1 not in keep_indices:
			new_indices.append(str(i+1))

	return del_item(groceries, entry_id, name, new_indices)


def clear_list(entry_id, name):
	# update list in db
	db.update({'grocery_list': []}, doc_ids=[entry_id])
	return name + " has cleared the list.\n"


def show_list(groceries):
	grocery_list = ''
	if groceries:
		for i in range(len(groceries)):
			grocery_list += str(i+1) + ". " + groceries[i] + "\n"
		return grocery_list
	else:
		return "*tumbleweed*\n"


@client.event
async def on_ready():
	print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):

	# filters out bot messages
	if message.author == client.user:
		return
	
	action_msg = ''
	help_msg = str("""
```Anything sent to this channel will be added to the grocery list!\n
Other commands:
[del #]:\n deletes item at # 
[del # # #]: \n deletes each item given
[keep #]: \n keeps item at # and deletes rest
[keep # # #]: \n keeps items given and deletes rest
[edit # newItem]:\n changes item at # to newItem
[clear]:\n clears list
[help]: \n displays [How to use] info```""")

	if (message.content == 'gro-setup'):

		guild_entry = db.get(q.guild_id == message.guild.id)

		# if guild is already in db, don't create a new channel.
		print(guild_entry)
		if not guild_entry == None:

			channel_exists = False
			for text_channel in message.guild.text_channels:
				if guild_entry['channel_id'] == text_channel.id:
					channel_exists = True

			if not channel_exists:
				await message.channel.send("A grocery list is already present in this server, but channel does not exist.\n"
				+ "A new channel will be created.")

				channelObject = await message.guild.create_text_channel('grocery-list')

				embed = discord.Embed(title="Fam Grocery List")
				embed.add_field(name="How to use:",value=help_msg,inline=False)
				retStr = str("```" + show_list(guild_entry['grocery_list']) + "```")
				embed.add_field(name="Grocery list:",value=retStr,inline=False)
				embed.color = discord.Color.blue()
				embed.set_footer(text=action_msg)

				messageObject = await channelObject.send(embed=embed)

				db.update({
					'guild_id': messageObject.guild.id, 
					'channel_id': channelObject.id, 
					'message_id': messageObject.id, 
					'grocery_list': []
					}, q.guild_id == messageObject.guild.id)

				print("Updating guild entry with id: " + str(messageObject.guild.id))

			else:
				await message.channel.send("A grocery list is already present in this server.")
				await message.delete()
			return

		
		# if it doesnt exist, create a new entry
		channelObject = await message.guild.create_text_channel('grocery-list')

		embed = discord.Embed(title="Fam Grocery List")
		embed.add_field(name="How to use:",value=help_msg,inline=False)
		retStr = str("```" + show_list(None) + "```")
		embed.add_field(name="Grocery list:",value=retStr,inline=False)
		embed.color = discord.Color.blue()
		embed.set_footer(text=action_msg)

		messageObject = await channelObject.send(embed=embed)

		# ids are integer types
		db.upsert({
			'guild_id': messageObject.guild.id, 
			'channel_id': channelObject.id, 
			'message_id': messageObject.id, 
			'grocery_list': []
			}, q.guild_id == messageObject.guild.id)

		print("Creating new guild entry with id: " + str(messageObject.guild.id))

	# if guild entry does not exist, we don't do anything.
	if db.get(q.guild_id == message.guild.id) == None:
		return

	# grab the db entry
	guild_entry = db.get(q.guild_id == message.guild.id)
	gro_channel = guild_entry['channel_id']
	gro_message = guild_entry['message_id']
	entry_id = guild_entry.doc_id

	if message.channel.id == gro_channel:
		grocery_channel = client.get_channel(gro_channel)
		grocery_message = await grocery_channel.fetch_message(gro_message)

		name = message.author.name
		embed = discord.Embed(title="Fam Grocery List")
		
		try:

			# get grocery list
			gro_list = db.get(doc_id=entry_id)['grocery_list'].copy()

			# delete
			if message.content.startswith('del '):
				index_str = message.content.split("del ",1)[1]
				indices = index_str.split()
				action_msg = del_item(gro_list, entry_id, name, indices)

			# keep
			elif message.content.startswith('keep '):
				index_str = message.content.split("keep ",1)[1]
				indices = index_str.split()
				action_msg = keep_item(gro_list, entry_id, name, indices)

			# edit
			elif message.content.startswith('edit '):
				argument_list = message.content.split("edit ",1)[1]
				arguments = argument_list.split(' ', 1)
				index = arguments[0]
				new_name = arguments[1]
				action_msg = edit_item(gro_list, entry_id, name, index, new_name)

			# clear
			elif message.content.startswith('clear'):
				action_msg = clear_list(entry_id, name)

			# help
			elif message.content.startswith('help'):
				embed.add_field(name="How to use:",value=help_msg,inline=False)
				action_msg = name + " forgot how to use the bot smh :("

			# add
			else:
				action_msg = add_item(gro_list, entry_id, name, message.content)

		except:
			action_msg = "Unexpected command: " + message.content

		gro_list = db.get(doc_id=entry_id)['grocery_list']
		retStr = str("```" + show_list(gro_list) + "```")
		embed.add_field(name="Grocery list:",value=retStr)
		embed.color = discord.Color.blue()
		embed.set_footer(text=action_msg)

		await grocery_message.edit(embed=embed)
		await message.delete()

client.run(os.environ['TOKEN'])