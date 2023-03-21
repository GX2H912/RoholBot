import json
import os
import random
from datetime import datetime
from typing import Optional

import discord
import openai
from discord.commands import Option
from discord.ext import commands
from dotenv import load_dotenv

from adjective_list import adjectives


class Embed:
    def __init__(self, title, description):
        self.embeds = None
        self.title = title
        self.description = description
        self.embed = discord.Embed(title=self.title, description=self.description,
                                   color=discord.Colour.dark_gold()).set_footer(
            text=f'Copyright {datetime.now().year} RoholWorks Inc. • {datetime.now().strftime("%m/%d/%Y")}')

    def without_fields(self) -> discord.Embed:
        return self.embed

    def reinitialize_embed(self):
        self.embed = discord.Embed(title=self.title, description=self.description,
                                   color=discord.Colour.dark_gold()).set_footer(
            text=f'Copyright {datetime.now().year} RoholWorks Inc. • {datetime.now().strftime("%m/%d/%Y")}')
        return self.embed

    def with_fields(self, fields) -> Optional[list[discord.Embed]]:
        self.embeds = []
        for index, (name, value) in enumerate(fields):
            if not self.embeds:
                self.embeds.append(self.embed)
            if index % 25 == 0 and index > 0:
                self.embeds.append(Embed.reinitialize_embed(self))
            self.embeds[-1].add_field(name=name, value=value, inline=False)
        return self.embeds


bot = commands.Bot(command_prefix='%', intents=discord.Intents.all())


@bot.event
async def on_ready():
    print('The RoholBot is ready.')


@bot.slash_command(name='rohol_qotd', description='Rohol quote(s) of the day.')
async def rohol_qotd(ctx: discord.context, show: Option(bool, 'Show quote(s) in chat?', default=False),
                     n: Option(int, 'Number of quotes', default=1)) -> None:
    def get_quote():
        with open('gatsby.txt', 'r') as fp:
            reader = [line for line in fp.readlines() if line != '\n']
        string = random.choice(reader)
        if len(string.split('.')) > 1:
            string = string[:string.find('.') + 1] + '.'
        while len(string) > 1024:
            string = random.choice(reader)
        start_quote = string[0] == '"'
        end_quote = string[-2] == '"'
        if start_quote or end_quote:
            if start_quote and end_quote:
                string = string[1:-2]
            elif end_quote:
                string = string[:-2]
            elif start_quote:
                string = string[1:-1]
        return f'"{string}"'

    date = datetime.now().strftime('%m/%d/%Y')

    def adjective():
        return ' '.join(s[0].upper() + s[1:] for s in str(random.choice(adjectives)).split('_'))

    await ctx.defer(ephemeral=(False if show else True))
    fields = ([f'The \'{adjective()}\' Rohol Quote{" (" + str(i + 1) + ")" if n > 1 else ""}:\n',
               f'{get_quote()}\n-Brent Rohol {date}'] for i in range(n))
    embeds = Embed(f'The {adjective()} Rohol Quote{"s" if n > 1 else ""} of {date}', None).with_fields(fields)
    for embed in embeds:
        await ctx.respond(embed=embed, ephemeral=(False if show else True))


@bot.slash_command(
    name='ask_rohol',
    description='Ask Rohol AI'
)
async def ask_rohol(
        ctx: discord.context, request: Option(str, 'Input prompt', required=True)
) -> None:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    await ctx.defer(ephemeral=True)
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=request,
        temperature=0.7,
        max_tokens=600,
        top_p=1,
    )
    output = response['choices'][0]['text']
    output_list = []
    op = list(range(0, len(output), 1021))
    greater_than_one = len(op) > 1
    for i, n in enumerate(op):
        affix = '...' if greater_than_one else ''
        if i + 1 < len(op):
            out = output[n:op[i + 1]].strip() + affix
        else:
            out = affix + output[n:len(output)].strip()
        output_list.append(out)
    fields = [[f'{f"Response (Page {n + 1})" if len(op) > 1 else "Response"}', text] for n, text in
              enumerate(output_list)]
    embed = Embed('Rohol AI', f'The answer to your prompt:').with_fields(fields)
    await ctx.respond(embed=embed[0], ephemeral=True)


if __name__ == '__main__':
    load_dotenv()
    bot.run(os.getenv('TOKEN'))
