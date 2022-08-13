from django.apps import AppConfig


class AuctionTableConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'trist_draft.apps.auction_table'

    def ready(self):
        import trist_draft.apps.auction_table.signals