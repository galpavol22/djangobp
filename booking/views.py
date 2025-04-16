from django.shortcuts import render, redirect, get_object_or_404 
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth.forms import PasswordChangeForm
from django.core.mail import send_mail
from django.http import HttpResponse

import stripe

from .forms import SignupForm
from .models import Room, Reservation, UserProfile, HotelInfo
stripe.api_key = 'sk_test_51R9vnDR9WeIkqu7ifVE4tBnWb31TN6JWQ1kjzfCJZK073hgDTIU88aL8EbjJJsG4dT3sQLRtSmkhDwFMvhhp2Gdi007r0K8O5l'


def index(request):
    return render(request, 'booking/index.html')


def about(request):
    return render(request, 'booking/about.html')


def gallery(request):
    return render(request, 'booking/gallery.html')


def kontakt(request):
    hotel_info = HotelInfo.objects.last()
    return render(request, 'booking/kontakt.html', {'hotel_info': hotel_info})


def ubytovanie(request):
    rooms = Room.objects.all()
    return render(request, 'booking/ubytovanie.html', {'rooms': rooms})


def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/admin/' if user.is_superuser else '/moj_ucet/')
        else:
            messages.error(request, "Nesprávne prihlasovacie údaje")
            return redirect('login')
    return render(request, 'booking/login.html')


@login_required
def create_reservation(request):
    if request.method == "POST":
        action = request.POST.get('action', '')
        if action == 'select_dates':
            check_in_str = request.POST.get('check_in')
            check_out_str = request.POST.get('check_out')
            if not (check_in_str and check_out_str):
                messages.error(request, "Prosím, zadajte dátum príchodu a odchodu.")
                return redirect('create_reservation')
            try:
                check_in_date = datetime.strptime(check_in_str, "%Y-%m-%d").date()
                check_out_date = datetime.strptime(check_out_str, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Neplatný formát dátumu.")
                return redirect('create_reservation')

            today = timezone.now().date()
            max_date = today + timedelta(days=3*365)
            if check_in_date < today or check_out_date < today:
                messages.error(request, "Nemôžete zadať minulé dátumy.")
                return redirect('create_reservation')
            if check_out_date <= check_in_date:
                messages.error(request, "Dátum odchodu musí byť neskôr ako dátum príchodu.")
                return redirect('create_reservation')
            if check_in_date > max_date or check_out_date > max_date:
                messages.error(request, "Rezerváciu je možné vytvoriť najviac 3 roky dopredu.")
                return redirect('create_reservation')

            available_rooms = Room.objects.exclude(
                reservation__check_in__lt=check_out_date,
                reservation__check_out__gt=check_in_date
            )
            return render(request, 'booking/reservation_form.html', {
                'rooms': available_rooms,
                'check_in': check_in_str,
                'check_out': check_out_str,
                'today': today.isoformat(),
                'max_date': max_date.isoformat()
            })

        elif action == 'reserve_room':
            room_id = request.POST.get('room_id')
            check_in_str = request.POST.get('check_in')
            check_out_str = request.POST.get('check_out')
            if not (room_id and check_in_str and check_out_str):
                messages.error(request, "Chýbajú údaje pre rezerváciu.")
                return redirect('create_reservation')

            room = get_object_or_404(Room, id=room_id)
            try:
                check_in_date = datetime.strptime(check_in_str, "%Y-%m-%d").date()
                check_out_date = datetime.strptime(check_out_str, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Neplatný formát dátumu.")
                return redirect('create_reservation')

            today = timezone.now().date()
            max_date = today + timedelta(days=3*365)
            if check_in_date < today or check_out_date < today:
                messages.error(request, "Nemôžete rezervovať izbu v minulosti.")
                return redirect('create_reservation')
            if check_in_date > max_date or check_out_date > max_date:
                messages.error(request, "Rezervácia nemôže byť viac ako 3 roky vopred.")
                return redirect('create_reservation')

            overlapping = Reservation.objects.filter(
                room=room,
                check_in__lt=check_out_date,
                check_out__gt=check_in_date
            )
            if overlapping.exists():
                messages.error(request, "Táto izba je v danom termíne už obsadená.")
                return redirect('create_reservation')

            days = (check_out_date - check_in_date).days
            total_price = days * room.price_per_night
            reservation = Reservation.objects.create(
                user=request.user,
                room=room,
                check_in=check_in_date,
                check_out=check_out_date,
                total_price=total_price
            )
            messages.success(request, "Rezervácia bola úspešne vytvorená.")
            return redirect('reservation_detail', reservation_id=reservation.id)
    else:
        today = timezone.now().date()
        max_date = today + timedelta(days=3*365)
        return render(request, 'booking/reservation_form.html', {
            'today': today.isoformat(),
            'max_date': max_date.isoformat()
        })


@login_required
def reservation_detail(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    return render(request, 'booking/reservation_detail.html', {'reservation': reservation})


def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            phone = form.cleaned_data.get('phone')

            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.phone = phone
            profile.save()

            send_mail(
                subject='Vitajte v hoteli Tatry!',
                message=f'Ahoj {user.username}, vitajte v našom hoteli. Tešíme sa na vašu návštevu!',
                from_email='hotel.tatry.noreply@gmail.com',
                recipient_list=[user.email],
                fail_silently=False,
            )

            login(request, user)
            return redirect('moj_ucet')
        else:
            print("Form is not valid:", form.errors)
    else:
        form = SignupForm()
    return render(request, 'booking/signup.html', {'form': form})


@login_required
def moj_ucet(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    reservations = Reservation.objects.filter(user=request.user)
    
    password_form = PasswordChangeForm(user=request.user, data=request.POST or None)
    if request.method == "POST" and 'change_password' in request.POST:
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Heslo bolo úspešne zmenené.")
            return redirect('moj_ucet')
    return render(request, 'booking/moj_ucet.html', {
        'user_profile': user_profile,
        'reservations': reservations,
        'password_form': password_form,
    })


@login_required
def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    return render(request, 'booking/room_detail.html', {'room': room})


@login_required
def cancel_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    if request.method == "POST":
        reservation.delete()
        messages.success(request, "Rezervácia bola zrušená.")
        return redirect('moj_ucet')
    return redirect('moj_ucet')


@login_required
def delete_account(request):
    if request.method == "POST":
        user = request.user
        user.delete()
        messages.success(request, "Váš účet bol úspešne odstránený.")
        return redirect('index')
    return redirect('moj_ucet')


@login_required
def stripe_payment(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)

    if reservation.is_paid:
        messages.info(request, "Táto rezervácia je už zaplatená.")
        return redirect('reservation_detail', reservation_id=reservation.id)

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'eur',
                'unit_amount': int(reservation.total_price * 100),
                'product_data': {
                    'name': f"Izba č. {reservation.room.room_number} ({reservation.check_in} – {reservation.check_out})",
                },
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri(f'/platba-uspesna/{reservation.id}/'),
        cancel_url=request.build_absolute_uri(f'/reservation/{reservation.id}/'),
        customer_email=request.user.email,
    )

    return redirect(session.url, code=303)


@login_required
def platba_uspesna(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)
    reservation.is_paid = True
    reservation.save()
    messages.success(request, "Platba prebehla úspešne. Ďakujeme!")
    return redirect('reservation_detail', reservation_id=reservation.id)
