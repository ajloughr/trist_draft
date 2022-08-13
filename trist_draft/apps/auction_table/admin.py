from django.contrib import admin

# Register your models here.
from .models import auction_user, auction_manager, nfl_player, drafted_player

admin.site.register(auction_user)
admin.site.register(auction_manager)
admin.site.register(nfl_player)
admin.site.register(drafted_player)