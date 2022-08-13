from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect

# Create your views here.
def login_view(request):
    if request.user.is_authenticated:
        return redirect('/auction')
    
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        #print(username, password)

        user = authenticate(request, username=username, password=password)
        if user is None:
            context = {"error" : "Invalid username or password"}
            return render(request,"accounts/login.html", context)
        
        login(request, user)

        return redirect('/')

    return render(request, "accounts/login.html", {})

def logout_view(request):
    logout(request)
    if request.method == "POST":
        logout(request)
        return redirect("/login")
        
    return render(request, "index.html", {})
    

def register_view(request):
    return render(request, "accounts/register.html", {})