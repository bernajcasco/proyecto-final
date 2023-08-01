from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.dates import YearArchiveView
from core import settings
from . import models, forms


class NotFoundView(TemplateView):
    template_name = "blog/404.html"


class InicioView(ListView):
    model: models.Articulo
    template_name = 'blog/inicio.html'
    context_object_name = 'articulos'
    paginate_by = 3
    queryset = models.Articulo.objects.filter(publicado=True)


class ArticuloDetailView(DetailView):
    model = models.Articulo
    template_name = 'blog/articulo.html'
    context_object_name = 'articulo'
    slug_field = 'slug'
    slug_url_kwarg = 'articulo_slug'


class ArticulosByCategoriaView(ListView):
    model = models.Categoria
    template_name = 'blog/categoria.html'
    context_object_name = 'articulos'
    paginate_by = 3

    def get_queryset(self):
        categoria_slug = self.kwargs['categoria_slug']
        categoria = get_object_or_404(models.Categoria, slug=categoria_slug)
        return models.Articulo.objects.filter(categoria=categoria, publicado=True)

    def get_context_data(self, **kwargs):
        context = super(ArticulosByCategoriaView,
                        self).get_context_data(**kwargs)
        context['categoria'] = models.Categoria.objects.get(
            slug=self.kwargs['categoria_slug'])
        return context


class ArticulosByAutorView(ListView):
    model = User
    template_name = 'blog/autor.html'
    context_object_name = 'articulos'
    paginate_by = 3

    def get_queryset(self):
        autor = self.kwargs['autor']
        autor = get_object_or_404(User, username=autor)
        return models.Articulo.objects.filter(autor=autor, publicado=True)

    def get_context_data(self, **kwargs):
        context = super(ArticulosByAutorView, self).get_context_data(**kwargs)
        context['autor'] = User.objects.get(username=self.kwargs['autor'])
        return context


class ArticulosByArchivoView(YearArchiveView):
    model = models.Articulo
    template_name = 'blog/archivo.html'
    make_object_list = True
    context_object_name = 'articulos'
    paginate_by = 3
    date_field = 'creacion'
    allow_future = False

    def get_queryset(self):
        year = self.kwargs['year']
        month = self.kwargs['month']

        if year and month:
            context = models.Articulo.objects.filter(
                creacion__year=year, creacion__month=month, publicado=True)
        else:
            context = super().get_queryset()
        return context

    def get_context_data(self, **kwargs):
        context = super(ArticulosByArchivoView,
                        self).get_context_data(**kwargs)
        year = self.kwargs['year']
        month = self.kwargs['month']

        if year and month:
            context['articulo_fecha'] = models.Articulo.objects.filter(
                creacion__year=year, creacion__month=month, publicado=True).first()

        return context


################# CRUD ####################

def usuario_es_colaborador(user):
    return user.groups.filter(name='colaborador').exists()


@method_decorator(user_passes_test(usuario_es_colaborador, login_url='login'), name='dispatch')
class ArticuloCreateView(CreateView):
    model = models.Articulo
    template_name = 'blog/forms/crear_articulo.html'
    form_class = forms.ArticuloForm
    

    def form_valid(self, form):
        form.instance.autor = self.request.user
        return super().form_valid(form)
    
    success_url = reverse_lazy('inicio')


@method_decorator(user_passes_test(usuario_es_colaborador, login_url='login'), name='dispatch')
class ArticuloUpdateView(UpdateView):
    model = models.Articulo
    template_name = 'blog/forms/actualizar_articulo.html'
    form_class = forms.ArticuloForm
    slug_field = 'slug'
    slug_url_kwarg = 'articulo_slug'

    def form_valid(self, form):
        if form.instance.autor == self.request.user or self.request.user.is_superuser:
            return super().form_valid(form)
        else:
            return redirect('login')

    def get_success_url(self):
        # Obtiene el artículo actualizado desde el contexto
        articulo = self.object
        # Genera la URL para la vista 'articulo' usando el slug actualizado del artículo
        return reverse('articulo', kwargs={'articulo_slug': articulo.slug})


@method_decorator(user_passes_test(usuario_es_colaborador, login_url='login'), name='dispatch')
class ArticuloDeleteView(DeleteView):
    model = models.Articulo
    template_name = 'blog/forms/eliminar_articulo.html'
    slug_field = 'slug'
    slug_url_kwarg = 'articulo_slug'
    success_url = reverse_lazy('inicio')

    def dispatch(self, request, *args, **kwargs):
        # Obtiene el artículo a eliminar desde la base de datos
        self.object = self.get_object()

        # Verifica si el usuario actual es el autor del artículo
        if self.object.autor == request.user or request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        else:
            # Si el usuario no es el autor, redirigir a la página de login
            return redirect('login')


class SignUpView(CreateView):
    template_name = 'registration/register.html'
    form_class = forms.RegisterUserForm
    # Cambiar 'login' por el nombre de la vista de inicio de sesión
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        # Guardar el usuario y configurar un mensaje de éxito
        response = super().form_valid(form)
        # Configurar la contraseña correctamente
        self.object.set_password(form.cleaned_data['password1'])
        # Marcar el usuario como inactivo hasta que confirme su correo electrónico
        self.object.is_active = False

        if not Group.objects.filter(name='miembro').exists():
            Group.objects.create(name='miembro')
            Group.objects.create(name='colaborador')

        self.object.groups.add(Group.objects.get(name='miembro'))
        self.object.save()

        # Generar el token de verificación
        token = default_token_generator.make_token(self.object)
        uid = urlsafe_base64_encode(force_bytes(self.object.pk))

        # Construir el enlace de confirmación
        confirmation_link = self.request.build_absolute_uri(
            reverse('confirmacion', kwargs={'code': token, 'user': uid})
        )

        # Enviar correo electrónico de confirmación
        subject = 'Confirmación de registro'
        message = render_to_string('registration/confirmation_email.html', {
            'user': self.object,
            'confirmation_link': confirmation_link,
        })
        send_mail(subject, message, settings.EMAIL_HOST_USER,
                  [self.object.email])

        return response


class ConfirmationView(View):
    def get(self, request, code, user):
        try:
            uid = urlsafe_base64_decode(user).decode('utf-8')
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            # Manejar enlace inválido o usuario no encontrado
            messages.error(request, "El enlace de confirmación es inválido.")
            # Redirigir a la página de inicio de sesión o donde desees
            return redirect('login')

        if default_token_generator.check_token(user, code):
            # Si el token es válido, confirmar al usuario y activar su cuenta
            user.is_active = True
            perfil = models.Perfil.objects.create(user=user)
            perfil.save()

            user.save()
            messages.success(
                request, "¡Tu cuenta ha sido activada! Ahora puedes iniciar sesión.")
        else:
            # Manejar token inválido
            messages.error(request, "El enlace de confirmación es inválido.")

        # Redirigir a la página de inicio de sesión o donde desees
        return redirect('login')