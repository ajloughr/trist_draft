from django.shortcuts import render, redirect, get_object_or_404

from .models import auction_user, auction_manager
from .forms import NewBidForm, AjaxNewBidForm
import uuid

from django.views.generic.edit import CreateView

from django.http import HttpResponse, JsonResponse

from django.db.models import Max

from django.contrib.auth.decorators import login_required

# Create your views here.
# @login_required(login_url='/login')
# def old_auction_table_view(request):
#     print("Updating Auction Table")
#     all_auction_users = auction_user.objects.all()
#     current_auction_manager = get_object_or_404(auction_manager,pk=1)

#     current_user_id = request.user.id
#     current_auction_user = auction_user.objects.filter(user_id=current_user_id)
#     print("Loading auction view for: " +str(current_auction_user.team_name))

#     form = NewBidForm(initial={'new_bid_uuid': uuid.uuid4()})

#     # print(str(request.POST))
#     # if 'submit_new_bid' in request.POST:
#     #     form = NewBidForm(request.POST)
#     #     new_bid_view(request,current_auction_user, current_auction_manager,form)
    

#     # if 'drop_out' in request.POST:
#     #     form = NewBidForm(request.POST)
#     #     drop_out_view(request,current_auction_user, current_auction_manager)
    
#     # if 'pass' in request.POST:
#     #     form = NewBidForm(request.POST)
#     #     pass_current_user(request,current_auction_user, current_auction_manager)

    
    

#     context = {
#         'auction_users_list': all_auction_users,
#         'current_auction_manager': current_auction_manager,
#         "current_auction_user":current_auction_user,
#         "form":form,
#     }

#     return render(request,"auction_table/auction_table.html",context)

@login_required(login_url='/login')
def auction_table_view(request):
    print("Loading Auction Table view")
    all_auction_users = auction_user.objects.all()
    current_auction_manager = get_object_or_404(auction_manager,pk=1)

    current_user_id = request.user.id
    is_user_admin = request.user.is_staff
    current_auction_user_query = auction_user.objects.filter(user_id=current_user_id)
    
    if len(current_auction_user_query) == 0:
        print("Loading auction view for: " +str(request.user.username))
        current_auction_user = "NA"
    else: 
        current_auction_user = current_auction_user_query[0]
        print("Loading auction view for: " +str(current_auction_user.team_name))
        

    context = {
        'auction_users_list': all_auction_users,
        'current_auction_manager': current_auction_manager,
        "current_auction_user":current_auction_user,
        'is_user_admin':is_user_admin
        # "form":form,
    }

    return render(request,"auction_table/auction_table.html",context)

def drop_out_view(request,current_auction_user,current_auction_manager):
    print(current_auction_user.team_name + " is dropping out")
    return redirect('/auction')

def return_to_auction(request):
    print("Returning to auction...")
    return redirect('/auction')


