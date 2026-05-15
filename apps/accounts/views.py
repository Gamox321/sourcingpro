from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordChangeView,
    PasswordResetView, PasswordResetConfirmView,
)
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .forms import LoginForm, PasswordChangeForm


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        if user.contrasena_temporal:
            login(self.request, user)
            messages.warning(
                self.request,
                'Debes cambiar tu contraseña temporal antes de continuar.'
            )
            return redirect('accounts:password_change')
        user.intentos_fallidos = 0
        user.save(update_fields=['intentos_fallidos'])
        return super().form_valid(form)

    def form_invalid(self, form):
        email = form.cleaned_data.get('username')
        if email:
            try:
                from .models import User
                user = User.objects.get(email=email)
                user.intentos_fallidos += 1
                user.save(update_fields=['intentos_fallidos'])
                intentos = user.intentos_fallidos
                if intentos >= 3:
                    messages.warning(
                        self.request,
                        f'Has tenido {intentos} intentos fallidos. '
                        'Verifica tus credenciales o contacta al administrador.'
                    )
                elif intentos >= 1:
                    messages.warning(
                        self.request,
                        f'Intento fallido #{intentos}.'
                    )
            except User.DoesNotExist:
                pass
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('accounts:login')


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    form_class = PasswordChangeForm
    template_name = 'accounts/password_change_form.html'
    success_url = reverse_lazy('accounts:password_change_done')

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.user.contrasena_temporal = False
        self.request.user.save(update_fields=['contrasena_temporal'])
        update_session_auth_hash(self.request, self.request.user)
        messages.success(self.request, 'Contraseña cambiada exitosamente.')
        return response


class PasswordChangeDoneView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/password_change_done.html'


class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset_form.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['user_roles'] = self.request.user.roles.all()
        from apps.notifications.models import Notification
        ctx['notificaciones_recientes'] = Notification.objects.filter(
            usuario_destinatario=self.request.user,
        ).order_by('-fecha_envio')[:10]
        return ctx
