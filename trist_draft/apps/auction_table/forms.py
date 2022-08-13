from django import forms

class NewBidForm(forms.Form):
    new_bid = forms.IntegerField(label="New Bid", widget=forms.NumberInput())
    new_bid_uuid = forms.UUIDField(widget=forms.HiddenInput())

class AjaxNewBidForm(forms.Form):

    new_bid = forms.IntegerField(label="New Bid", widget=forms.NumberInput())
    new_bid_uuid = forms.UUIDField(widget=forms.HiddenInput())