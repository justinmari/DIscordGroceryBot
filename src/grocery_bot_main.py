import discord
import os
#from grocery_bot_db import *
from dotenv import load_dotenv

load_dotenv()
client = discord.Client()

def table_to_list(table):
	result = []
	table_items = table.all()
	for i in range(len(table_items)):
		result.append(table_items[i]['item'])
	return result

def add_item(name, item):
	global groceries
	groceries.append(item)
	return name + " added [" + item + "] to the list.\n"

def edit_item(name, index, new_name):
	global groceries

	if (not index.isnumeric() and int(index)-1 >= len(groceries)):
		return index + " is not a valid index.\n"

	item = groceries[int(index)-1]
	groceries[int(index)-1] = new_name
	return name + " changed [" + item + "] to [" + new_name + "].\n"

def del_item(name, indices):
	global groceries

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

	return msg

def keep_item(name, indices):
	global groceries

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

	print(new_indices)

	return del_item(name, new_indices)

def clear_list(name):
	global groceries
	groceries = []
	return name + " has cleared the list.\n"

def show_list():
	global groceries
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

	global groChannel
	global groMessage

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

	if message.channel.id == groChannel:
		grocery_channel = client.get_channel(groChannel)
		grocery_message = await grocery_channel.fetch_message(groMessage)

		name = message.author.name
		embed = discord.Embed(title="Fam Grocery List")
		
		try:

			# delete
			if message.content.startswith('del '):
				index_str = message.content.split("del ",1)[1]
				indices = index_str.split()
				action_msg = del_item(name, indices)

			# keep
			elif message.content.startswith('keep '):
				index_str = message.content.split("keep ",1)[1]
				indices = index_str.split()
				action_msg = keep_item(name, indices)

			# edit
			elif message.content.startswith('edit '):
				argument_list = message.content.split("edit ",1)[1]
				arguments = argument_list.split()
				index = arguments[0]
				new_name = arguments[1]
				action_msg = edit_item(name, index, new_name)

			# clear
			elif message.content.startswith('clear'):
				action_msg = clear_list(name)

			# help
			elif message.content.startswith('help'):
				embed.add_field(name="How to use:",value=help_msg,inline=False)
				action_msg = name + " forgot how to use the bot smh :("

			# add
			else:
				action_msg = add_item(name, message.content)

		except:
			action_msg = "Unexpected command: " + message.content

		retStr = str("```" + show_list() + "```")
		embed.add_field(name="Grocery list:",value=retStr)
		embed.color = discord.Color.blue()
		embed.set_footer(text=action_msg)

		await grocery_message.edit(embed=embed)
		await message.delete()

	if message.content == 'gro-setup':
		channelObject = await message.guild.create_text_channel('grocery-list')

		embed = discord.Embed(title="Fam Grocery List")
		embed.add_field(name="How to use:",value=help_msg,inline=False)
		retStr = str("```" + show_list() + "```")
		embed.add_field(name="Grocery list:",value=retStr,inline=False)
		embed.color = discord.Color.blue()
		embed.set_footer(text=action_msg)

		messageObject = await channelObject.send(embed=embed)
		groChannel = channelObject.id
		groMessage = messageObject.id

# db = init_db()
# id_table = db.table('ids')
# groceries_table = db.table('groceries')
# groceries_table.insert({'item': 'bananas'})

groChannel = None
groMessage = None
groceries = [] #table_to_list(groceries_table)

client.run(os.environ['TOKEN'])