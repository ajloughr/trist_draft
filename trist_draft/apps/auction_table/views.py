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
        
    
    
    

    # form = NewBidForm(initial={'new_bid_uuid': uuid.uuid4()})

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

# def pass_current_user(request,current_auction_user,current_auction_manager):
#     print("current_auction_user.last_bid_uuid: " + str(current_auction_user.last_bid_uuid))
#     print("new_bid_uuid: " + str(request.POST.get("new_bid_uuid")))
#     if current_auction_manager.active_bidder == current_auction_user.draft_order:
#         if current_auction_user.pass_available == True:
#             print("Passing current team: " + current_auction_user.team_name)
#             current_auction_user.pass_available = False
#             current_auction_manager.active_bidder = current_auction_manager.active_bidder + 1
#             current_auction_user.save()
#             current_auction_manager.save()
#         else:
#             print("User does not have pass available")
#     else:
#         print("It is not your turn to pass!")

# def new_bid_view(request,current_auction_user,current_auction_manager,form):

#     if request.method == 'POST':
#         print('New Bid POST')
        
#         print("current_auction_user.last_bid_uuid: " + str(current_auction_user.last_bid_uuid))
#         print("new_bid_uuid: " + str(request.POST.get("new_bid_uuid")))

#         if form.is_valid():
#             print("current_auction_user.current_bid: " + str(current_auction_user.current_bid))
#             if current_auction_manager.active_bidder == current_auction_user.draft_order:
#                 if str(current_auction_user.last_bid_uuid) != str(request.POST.get("new_bid_uuid")):
#                     current_auction_user.current_bid = request.POST.get("new_bid")
#                     current_auction_manager.active_bidder = current_auction_manager.active_bidder + 1
#                     current_auction_user.last_bid_uuid = request.POST.get("new_bid_uuid")
#                     max_bidder_index = auction_user.objects.aggregate(Max('draft_order'))["draft_order__max"]
#                     if current_auction_manager.active_bidder > max_bidder_index:
#                         current_auction_manager.active_bidder = 1

#                     print("max_bidder_index: " + str(max_bidder_index))
#                     print("New Bid: " + str(request.POST.get("new_bid")))
#                     current_auction_user.save()
#                     current_auction_manager.save()
#                     form = NewBidForm(initial={'new_bid_uuid': uuid.uuid4()})
                    
#                     return redirect('/auction')
#                 else:
#                     print("Submitted bid has the same UUID as the last bid, ignoring")
#             else:
#                 print("It is not the current users turn to bid")
            

#     else:
#         print('New Bid NOT POST')
#         form = NewBidForm(initial={'new_bid_uuid': uuid.uuid4()})
    
#     context = {
#         "form":form,
#         "current_auction_user":current_auction_user
#     }
#     return render(request,"auction_table/auction_table.html", context)


# def ajax_auction_table(request):
#     print("Init ajax auction table")
#     if request.is_ajax and request.method == "GET":
#         print("We are get and AJAX")
#         form = NewBidForm(initial={'new_bid_uuid': uuid.uuid4()})
#         all_auction_users = auction_user.objects.all()
#         current_auction_manager = get_object_or_404(auction_manager,pk=1)

#         current_user_id = request.user.id
#         current_auction_user = get_object_or_404(auction_user,user_id=current_user_id)

#         test_data = request.GET.get("test")
#         print("Got AJAX data: " + str(test_data))
#         context = {
#             'auction_users_list': all_auction_users,
#             'current_auction_manager': current_auction_manager,
#             "current_auction_user":current_auction_user,
#             "form":form,
#         }
        
#         return JsonResponse({"current_auction_user_team":current_auction_user.team_name}, status = 200)

#     return JsonResponse({}, status = 400)

# def trigger_ajax(request):
#     if request.is_ajax and request.method == "GET":
#         return HttpResponse("Success!") # Sending an success response
#     else:
#             return HttpResponse("Request method is not a GET")

# def ajax_new_bid_view(request):
#     form = NewBidForm(initial={'new_bid_uuid': uuid.uuid4()})
#     if request.method == 'POST':
#         print('AJAX New Bid POST')
        
#         #print("current_auction_user.last_bid_uuid: " + str(current_auction_user.last_bid_uuid))
#         #print("new_bid_uuid: " + str(request.POST.get("new_bid_uuid")))

#         if form.is_valid():
#             print("form is valid")
#             #print("current_auction_user.current_bid: " + str(current_auction_user.current_bid))
#             #if current_auction_manager.active_bidder == current_auction_user.draft_order:
#                 #if str(current_auction_user.last_bid_uuid) != str(request.POST.get("new_bid_uuid")):
#                     #current_auction_user.current_bid = request.POST.get("new_bid")
#                     #current_auction_manager.active_bidder = current_auction_manager.active_bidder + 1
#                     #current_auction_user.last_bid_uuid = request.POST.get("new_bid_uuid")
#                     #max_bidder_index = auction_user.objects.aggregate(Max('draft_order'))["draft_order__max"]
#                     #if current_auction_manager.active_bidder > max_bidder_index:
#                     #    current_auction_manager.active_bidder = 1

#                     #print("max_bidder_index: " + str(max_bidder_index))
#                     #print("New Bid: " + str(request.POST.get("new_bid")))
#                     #current_auction_user.save()
#                     #current_auction_manager.save()
#                     #form = NewBidForm(initial={'new_bid_uuid': uuid.uuid4()})
                    
#             #         return redirect('/auction/return-to-auction')
#             #     else:
#             #         print("Submitted bid has the same UUID as the last bid, ignoring")
#             # else:
#             #     print("It is not the current users turn to bid")
            

#     else:
#         print('New Bid NOT POST')
#         #form = NewBidForm(initial={'new_bid_uuid': uuid.uuid4()})
    
#     context = {
#         "form":form,
#         #"current_auction_user":current_auction_user
#     }
#     return render(request,"auction_table/ajax_bid_menu.html", context)

# def check_ajax_stuff(request):
#     print("Checking ajax stuff")
#     submitted_bid = request.GET.get('bid_check', None)
#     data = {
#         'bid_check_data': str(submitted_bid) + " verified!" 
#     }
#     return JsonResponse(data)

