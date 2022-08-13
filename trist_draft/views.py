from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth import logout as auth_logout

def index(request):
    return render(request, 'index.html')