import json
import random
import string
import user_agents
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Link, ClickEvent
from django.db.models import Count
from django.core.paginator import Paginator
from django.db.models.functions import TruncDate


def generate_short_code(length=6):
    """Genera un código aleatorio de la longitud especificada."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def shorten_url(request):
    if request.method == 'POST':
        original_url = request.POST.get('original_url')
        if not original_url:
            return HttpResponseBadRequest("Debe proporcionar una URL.")

        short_code = generate_short_code()  # Función que genera el código aleatorio
        while Link.objects.filter(short_code=short_code).exists():
            short_code = generate_short_code()

        user = request.user if request.user.is_authenticated else None

        link = Link.objects.create(
            original_url=original_url,
            short_code=short_code,
            user=user
        )

        context = {
            'link': link,
            'short_domain': settings.SHORT_URL_DOMAIN,  # Dominio configurado
            'scheme': request.scheme,  # http o https, según corresponda
        }
        return render(request, 'core/shorten_success.html', context)

    return render(request, 'core/shorten_form.html')


def redirect_link(request, short_code):
    link = get_object_or_404(Link, short_code=short_code)

    if link.is_expired():
        return HttpResponse("Este enlace ha expirado.", status=410)

    # Registrar el clic (obteniendo datos como IP, user-agent, etc.)
    ClickEvent.objects.create(
        link=link,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        referrer=request.META.get('HTTP_REFERER')
    )

    return redirect(link.original_url)


@login_required
def my_links(request):
    enlaces_qs = Link.objects.filter(user=request.user).order_by('-created_at')

    total_links = enlaces_qs.count()
    total_clicks = sum(link.clicks.count() for link in enlaces_qs)

    paginator = Paginator(enlaces_qs, 10)
    page_number = request.GET.get('page')
    enlaces = paginator.get_page(page_number)

    context = {
        'enlaces': enlaces,
        'total_links': total_links,
        'total_clicks': total_clicks,
    }

    return render(request, 'core/my-links.html', context)


@login_required
def link_stats(request, pk):
    # 📌 Verifica que el enlace pertenezca al usuario autenticado
    link = get_object_or_404(Link, pk=pk, user=request.user)

    # 📊 Total de clics
    total_clicks = link.clicks.count()

    # 📅 Clics diarios
    daily_clicks = list(
        link.clicks.values('clicked_at__date')
        .annotate(click_count=Count('id'))
        .order_by('clicked_at__date')
    )

    # 🌍 Clics por país (Se asume que en el futuro se capturará la IP y se resolverá a país)
    country_clicks = link.clicks.values('ip_address').annotate(count=Count('id'))
    country_data = {entry['ip_address']: entry['count'] for entry in country_clicks if entry['ip_address']}

    # 📡 Ubicación geográfica (En este caso, usa solo IPs almacenadas)
    map_clicks = list(link.clicks.values('ip_address').annotate(count=Count('id')))

    # 📱 Dispositivos utilizados (Extraídos desde user_agent)
    device_clicks = {}
    browser_clicks = {}

    for event in link.clicks.values('user_agent').annotate(count=Count('id')):
        if event['user_agent']:
            ua = user_agents.parse(event['user_agent'])
            device_type = "Móvil" if ua.is_mobile else "Tablet" if ua.is_tablet else "Escritorio"
            browser = ua.browser.family

            # Agregar conteo de dispositivos
            device_clicks[device_type] = device_clicks.get(device_type, 0) + event['count']
            browser_clicks[browser] = browser_clicks.get(browser, 0) + event['count']

    # 📡 Enviar los datos al template
    context = {
        'link': link,
        'total_clicks': total_clicks,
        'unique_countries': len(country_data),
        'unique_devices': len(device_clicks),
        'daily_clicks': daily_clicks,
        'country_clicks': json.dumps(country_data),
        'map_clicks': json.dumps(map_clicks),
        'device_clicks': json.dumps(device_clicks),
        'browser_clicks': json.dumps(browser_clicks),
    }

    return render(request, 'core/link_stats.html', context)


@login_required
def global_stats(request):
    # 📌 Filtrar todos los enlaces del usuario autenticado
    enlaces = Link.objects.filter(user=request.user)
    total_links = enlaces.count()

    # 📊 Clics totales de todos los enlaces del usuario
    total_clicks = ClickEvent.objects.filter(link__in=enlaces).count()

    # 📅 Clics diarios (usamos `TruncDate` en lugar de `.extra()`)
    daily_clicks = list(
        ClickEvent.objects.filter(link__in=enlaces)
        .annotate(day=TruncDate('clicked_at'))
        .values('day')
        .annotate(click_count=Count('id'))
        .order_by('day')
    )

    # 🌍 Clics por país
    country_clicks = ClickEvent.objects.filter(link__in=enlaces).values('ip_address').annotate(count=Count('id'))
    country_data = {entry['ip_address']: entry['count'] for entry in country_clicks if entry['ip_address']}

    # 🗺️ Ubicación geográfica (basado en IP)
    map_clicks = list(ClickEvent.objects.filter(link__in=enlaces).values('ip_address').annotate(count=Count('id')))

    # 📱 Dispositivos utilizados
    device_clicks = {}
    browser_clicks = {}

    for event in ClickEvent.objects.filter(link__in=enlaces).values('user_agent').annotate(count=Count('id')):
        if event['user_agent']:
            ua = user_agents.parse(event['user_agent'])
            device_type = "Móvil" if ua.is_mobile else "Tablet" if ua.is_tablet else "Escritorio"
            browser = ua.browser.family

            # Agregar conteo de dispositivos
            device_clicks[device_type] = device_clicks.get(device_type, 0) + event['count']
            browser_clicks[browser] = browser_clicks.get(browser, 0) + event['count']

    # 📡 Enviar los datos al template
    context = {
        'total_links': total_links,
        'total_clicks': total_clicks,
        'unique_countries': len(country_data),
        'daily_clicks': daily_clicks,
        'country_clicks': json.dumps(country_data),
        'map_clicks': json.dumps(map_clicks),
        'device_clicks': json.dumps(device_clicks),
        'browser_clicks': json.dumps(browser_clicks),
    }

    return render(request, 'core/global_stats.html', context)
