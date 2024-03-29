import discord


class PageNumberModal(discord.ui.Modal, title="Enter a page number"):
    number = discord.ui.TextInput(label="Number")  # type: ignore

    def __init__(self, max_number):
        super().__init__(timeout=None)
        self.max_number = max_number
        self.number.placeholder = f'1-{max_number}'
        self.final_value = None

    async def on_submit(self, interaction: discord.Interaction):
        try:
            self.final_value = int(self.number.value)
        except ValueError:
            pass

        await interaction.response.defer()  # type: ignore


class Pages(discord.ui.View):
    def __init__(self, pages: list[discord.Embed], start_page: int = 0):
        assert len(pages) > 0, "You must provide at least one page"
        super().__init__()

        self.pages = pages
        self.page_count = len(pages)

        if self.page_count == 1:
            self.goto.disabled = True

        self.current_page = self.clamp_index(start_page)
        self.original_response = None

    async def show(self, interaction: discord.Interaction):
        await self.show_page(self.current_page, interaction, first_interaction=True)

    async def on_timeout(self):
        self.clear_items()
        await self.original_response.edit(view=self)

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="⏮")
    async def first(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self.show_page(0, interaction)

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="⬅")
    async def previous(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self.show_page(self.current_page - 1, interaction)

    @discord.ui.button(style=discord.ButtonStyle.blurple)
    async def goto(self, interaction: discord.Interaction, _: discord.ui.Button):
        modal = PageNumberModal(self.page_count)
        await interaction.response.send_modal(modal)  # type: ignore
        await modal.wait()

        page_number = modal.final_value
        if page_number is None or page_number < 1 or page_number > self.page_count:
            return await interaction.followup.send(  # type: ignore
                f"Invalid page number. Please enter a number between 1 and {self.page_count}",
                ephemeral=True
            )

        await self.show_page(page_number - 1, interaction, first_interaction=False, defer_on_edit=False)

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="➡")
    async def next(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self.show_page(self.current_page + 1, interaction)

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="⏭")
    async def last(self,  interaction: discord.Interaction, _: discord.ui.Button):
        await self.show_page(self.page_count - 1, interaction)

    async def show_page(
            self, index: int, interaction: discord.Interaction,
            first_interaction: bool = False, defer_on_edit: bool = True
    ):
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
            self.original_response = await interaction.original_response()
        else:
            await interaction.message.edit(embed=self.pages[self.current_page], view=self)
            if defer_on_edit:
                await interaction.response.defer()  # type: ignore

    def clamp_index(self, index: int):
        return min(max(index, 0), self.page_count - 1)
