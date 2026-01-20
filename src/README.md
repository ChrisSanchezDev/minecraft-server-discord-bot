# discord_bot.py

Future idea:

    Stop Server button for when no one is on the server (Maybe we can have it so if you have a specific role, you can turn it off at anytime)

        @discord.ui.button(label='Stop Server', style=discord.ButtonStyle.red, custom_id='stop_btn', emoji='⛔')
        async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            # Gives a defer message to discord (it asks for Discord to wait longer for a response)
            await interaction.response.defer(ephemeral=True)

            if display_status != 'online':
                button.disabled = True

            send_magic_packet(MSI_MAC)

            await interaction.followup.send(
                'Magic Packet sent! The server is waking up. The dashboard will update shortly.',
                ephemeral=True
            )

            embed = create_status_embed(display_status='booting')

            button.disabled = True # ??? Does this gray out the button?
            await interaction.message.edit(embed=embed, view=self)