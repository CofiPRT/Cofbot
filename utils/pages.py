import discord


class PageNumberModal(discord.ui.Modal, title="Enter a page number"):
    number = discord.ui.TextInput(label="Number")  # type: ignore

    def __init__(self, max_number, callback_func):
        super().__init__(timeout=None)
        self.max_number = max_number
        self.number.placeholder = f'1-{max_number}'
        self.callback_func = callback_func

    async def on_submit(self, interaction: discord.Interaction):
        page_number = int(self.number.value)

        if page_number < 1 or page_number > self.max_number:
            return await interaction.response.send_message(  # type: ignore
                f"Invalid page number. Please enter a number between 1 and {self.max_number}",
                ephemeral=True
            )

        await interaction.response.defer()  # type: ignore
        await self.callback_func(int(self.number.value))


class Pages(discord.ui.View):
    def __init__(self, pages: list[discord.Embed], start_page: int = 0):
        assert len(pages) > 0, "You must provide at least one page"
        super().__init__()

        self.pages = pages
        self.page_count = len(pages)

        if self.page_count == 1:
            self.goto.disabled = True

        self.current_page = self.clamp_index(start_page)

    async def show(self, interaction: discord.Interaction):
        await self.show_page(self.current_page, interaction, first_interaction=True)

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="⏮")
    async def first(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self.show_page(0, interaction)

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="⬅")
    async def previous(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self.show_page(self.current_page - 1, interaction)

    @discord.ui.button(style=discord.ButtonStyle.blurple)
    async def goto(self, interaction: discord.Interaction, _: discord.ui.Button):
        async def callback_func(page_number: int):
            await self.show_page(page_number - 1, interaction)

        await interaction.response.send_modal(PageNumberModal(self.page_count, callback_func))  # type: ignore

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="➡")
    async def next(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self.show_page(self.current_page + 1, interaction)

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="⏭")
    async def last(self,  interaction: discord.Interaction, _: discord.ui.Button):
        await self.show_page(self.page_count - 1, interaction)

    async def show_page(self, index: int, interaction: discord.Interaction, first_interaction: bool = False):
        self.current_page = self.clamp_index(index)
        self.goto.label = f"{self.current_page + 1}/{self.page_count}"

        is_first_page = self.current_page == 0
        self.first.disabled = is_first_page
        self.previous.disabled = is_first_page

        is_last_page = self.current_page == self.page_count - 1
        self.last.disabled = is_last_page
        self.next.disabled = is_last_page

        if first_interaction:
            await interaction.response.send_message(embed=self.pages[self.current_page], view=self)  # type: ignore
        else:
            await interaction.message.edit(embed=self.pages[self.current_page], view=self)
            await interaction.response.defer()  # type: ignore

    def clamp_index(self, index: int):
        return min(max(index, 0), self.page_count - 1)
