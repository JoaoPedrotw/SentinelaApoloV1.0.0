# D:\SentinelaApolo\Login\views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import LoginForm

def login_view(request):
    """
    View para a página de login.
    Autentica o usuário sem usar reCAPTCHA.
    """
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            # Captura username/password
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Autentica o usuário
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, "Login bem-sucedido!")
                return redirect('home')
            else:
                messages.error(request, "Credenciais inválidas.")
                return render(request, 'login/login.html', {'form': form})
        else:
            # Formulário inválido
            messages.error(request, "Erro no formulário. Verifique os campos.")
            return render(request, 'login/login.html', {'form': form})
    else:
        form = LoginForm()
        return render(request, 'login/login.html', {'form': form})

def logout_view(request):
    """
    View para encerrar a sessão do usuário.
    """
    logout(request)
    messages.success(request, "Você foi desconectado com sucesso.")
    return redirect('login')