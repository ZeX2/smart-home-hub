from notion_client import Client

from .note_id import NOTION_TOKEN
from .note_id import PAGE_ID

# I don't think you can really call this an API
class NotionNoteApi():
    def __init__(self):
        self.notion = Client(auth=NOTION_TOKEN)

    def get_note(self):
        notes = []
        page_blocks = self.notion.blocks.children.list(PAGE_ID, page_size=100)['results']
        for block in page_blocks:
            block_type = block['type']
            # Blocks like dividers have no text, and styled text comes in several pieces
            rich_text = block[block_type].get('rich_text')
            if rich_text:
                notes.append(''.join(text.get('plain_text', '') for text in rich_text))

        return '\n'.join(notes)
