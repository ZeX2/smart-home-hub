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
            if block[block_type]['rich_text']:
                notes.append(block[block_type]['rich_text'][0].get('plain_text', ''))

        return '\n'.join(notes)
