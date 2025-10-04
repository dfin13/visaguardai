from django.shortcuts import render

# Create your views here.
def home(request):
    from dashboard.models import Config
    config = Config.objects.first()
    price = config.price_dollars if config else 0
    price_cents = config.Price if config else 0
    return render(request, 'home.html', {'price': price, 'price_cents': price_cents})

