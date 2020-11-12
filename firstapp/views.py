from django.shortcuts import (get_object_or_404,render,HttpResponseRedirect)
from forms.form1 import form_registrations
from .models import events, registration, date_revenue, society_leads, state_connection, coupons
from .forms import eventsForm
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate,login, logout
import xlwt
from django.views.decorators.csrf import csrf_exempt
from paytm import checksum
from datetime import datetime, timedelta
from django.db.models.functions import TruncDay
from django.db.models import Count
import random
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pytz
import yagmail
# Create your views here.

def index(request):
    return render(request, 'index.html')

def other_states(request):
    if request.method == "POST":
        state_name = request.POST.get('state_select')
        state_con = state_connection.objects.get(state_name = state_name)
        return event_page(request, state_con.state_connected_to)
    states = state_connection.objects.all()
    return render(request, 'other_states.html', {'states' : states})

def event_page(request, state):
    if '_' in state:
        state = state.replace('_', ' ')
    cluster1 = events.objects.filter(select_state = state, cluster = 1)
    cluster2 = events.objects.filter(select_state = state, cluster = 2)
    return render(request, 'events.html', {'cluster1' : cluster1, 'cluster2' : cluster2})

def event_details(request, event_name):
    current_event = events.objects.get(name = event_name)
    return render(request, 'event_details.html', {'event' : current_event})

def main_form(request, event_name):
    if request.method == "POST":
        current_registration = form_registrations(data = request.POST)
        if current_registration.is_valid():
            name = request.POST.get('name')
            email = request.POST.get('email')
            number = request.POST.get('number')
            link = request.POST.get('link')
            event = request.POST.get('event')
            cost = request.POST.get('cost')
            referral = request.POST.get('referral')
            coupon = request.POST.get('coupon')
            timestamp = datetime.now()
            cr = registration(name=name, email=email, number=number, link=link, event=event, cost=cost,
                              referral=referral, coupon=coupon, timestamp=timestamp)
            cr.save()
            current_event = events.objects.get(name = event)
            if(current_event.cost == 0):
                text = "Hey, {name}\nYou have been registered for {event_name}.\nYour participant ID is: {participant_id}.\n"
                text = text.format(name=cr.name, event_name=cr.event,
                                   participant_id=cr.id)
                cr.participant_id = cr.id
                cr.save()
                yag = yagmail.SMTP(user=current_event.email, password=current_event.password)
                yag.send(
                    to=cr.email,
                    subject=cr.event + " Registration",
                    contents=text
                )
                print("cost 0")
                return render(request, 'paytm_status.html',
                              {'result': True, 'details': cr, 'state': current_event.select_state})
            else:
                cr.participant_id = cr.id
                cr.save()
                return render(request, 'paytm_status.html',
                              {'result': False, 'details': cr, 'state': current_event.select_state})
            if(current_event.group_event):
                if(int(cost) != current_event.cost and int(cost) !=current_event.cost2 ):
                    print("group")
                    return render(request, 'paytm_status.html',
                                  {'result': False, 'details': cr, 'state': current_event.select_state})
            else:
                if (len(coupon)>0):
                    c = coupons.objects.filter(event = current_event.id).filter(code = coupon).values('discount_amount')
                    print(c)
                    if c:
                        if(int(cost) != int(int(current_event.cost)-int(c[0]['discount_amount'])) and int(cost) != current_event.cost):
                            return render(request, 'paytm_status.html',
                                          {'result': False, 'details': cr, 'state': current_event.select_state})
                else:
                    if (int(cost) != current_event.cost):
                        return render(request, 'paytm_status.html',
                                      {'result': False, 'details': cr, 'state': current_event.select_state})
            param_dict = {
                'MID': 'FDFLnc15559267363390',
                'ORDER_ID': str(cr.id),
                'TXN_AMOUNT': str(cr.cost),
                'CUST_ID': str(cr.email),
                'INDUSTRY_TYPE_ID': 'Retail',
                'WEBSITE': 'DEFAULT',
                'CHANNEL_ID': 'WEB',
                'CALLBACK_URL': 'https://youthindiaevents.com/paytm_gateway/',
            }
            param_dict['CHECKSUMHASH'] = checksum.generate_checksum(param_dict, '89tbzmH&2RlSIKL#')
            return render(request, 'paytm.html', {'param_dict' : param_dict})
        else:
            current_event = events.objects.get(name=event_name)
            all_coupons = coupons.objects.filter(event=current_event.id, active=True)
            if (current_event.group_event):
                return render(request, 'form.html',
                              {'form': current_registration, 'event_name': current_event.name, 'event_cost': str(current_event.cost),
                               'group': True, 'cost2': str(current_event.cost2), 'coupons' : all_coupons})
            else:
                return render(request, 'form.html',
                              {'form': current_registration, 'event_name': current_event.name, 'event_cost': current_event.cost,
                               'group': False,'cost2' : current_event.cost, 'coupons' : all_coupons})
    current_event = events.objects.get(name = event_name)
    intital_dict = {'event' : current_event.name, 'cost' : current_event.cost}
    form = form_registrations(initial = intital_dict)
    all_coupons = coupons.objects.filter(event = current_event.id, active = True)
    if(current_event.group_event):
        return render(request, 'form.html',{ 'form' : form, 'event_name': current_event.name,'event_cost': str(current_event.cost),
                                         'group' : True, 'cost2' : str(current_event.cost2), 'coupons' : all_coupons})
    else:
        return render(request, 'form.html',
                      {'form': form, 'event_name': current_event.name, 'event_cost': current_event.cost,
                       'group': False,'cost2':current_event.cost,  'coupons' : all_coupons})


@csrf_exempt
def paytm_gateway(request):
    MERCHANT_KEY = '89tbzmH&2RlSIKL#'
    form = request.POST
    response_dict = {}
    for i in form.keys():
        response_dict[i] = form[i]
        if i == 'CHECKSUMHASH':
            Checksum = form[i]
    paid_registration = registration.objects.get(id=int(response_dict['ORDERID']))
    verify = checksum.verify_checksum(response_dict, MERCHANT_KEY, Checksum)
    if verify:
        if response_dict['RESPCODE'] == '01':
            paid_registration = registration.objects.get(id = int(response_dict['ORDERID']))
            paid_registration.mi_id = response_dict['MID']
            paid_registration.transaction_id = response_dict['TXNID']
            paid_registration.participant_id = response_dict['ORDERID']
            paid_registration.save()
            event_registered = events.objects.get(name = paid_registration.event)
            current_date_revenue = date_revenue.objects.filter(event_key = event_registered.id, day = datetime.today().date())
            if not paid_registration.paid:
                if not current_date_revenue:
                    new_date_revenue = date_revenue()
                    new_date_revenue.event_key = events.objects.get(name = paid_registration.event)
                    new_date_revenue.day = datetime.today().date()
                    new_date_revenue.no_of_participants = 1
                    new_date_revenue.revenue = int(paid_registration.cost)
                    new_date_revenue.save()
                else:
                    current_date_revenue[0].no_of_participants += 1
                    current_date_revenue[0].revenue += int(paid_registration.cost)
                    current_date_revenue[0].save()
            paid_registration.paid = True
            paid_registration.save()
            text = "Hey, {name}\nYou have been registered for {event_name}.\nYour participant ID is: {participant_id}.\n"
            text = text.format(name=paid_registration.name, event_name=paid_registration.event,
                               participant_id=paid_registration.participant_id)
            yag = yagmail.SMTP(user=event_registered.email, password=event_registered.password)
            yag.send(
                to=paid_registration.email,
                subject=paid_registration.event + " Registration",
                contents=text
            )
            state = events.objects.get(name = paid_registration.event).select_state
            return render(request, 'paytm_status.html', {'result' : True, 'details': paid_registration, 'state':state})
        else:
            paid_registration.coupon += response_dict['RESPCODE']
            paid_registration.save()
            state = events.objects.get(name=paid_registration.event).select_state
            return render(request, 'paytm_status.html', {'result' : False,  'state':state})


def society_leads_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username = username,password = password)

        if user:
            if user.is_active:
                login(request, user)
                society_lead = society_leads.objects.get(user=user)
                date_revenues = date_revenue.objects.filter(event_key = society_lead.event)
                event_name = society_lead.event.name
                total_revenue = 0
                total_participants = 0
                for j in date_revenues:
                    total_revenue += j.revenue
                    total_participants += j.no_of_participants
                return render(request, 'download_excel.html', {'event_name' : event_name, 'date_revenues' : date_revenues,
                                                               'total_revenue' : total_revenue , 'total_participants': total_participants})

            else:
                return HttpResponse('Wrong Login Credentials')
        else:
            return HttpResponse('Wrong Login Credentials')
    else:
        return render(request, 'login_form.html')


def admin_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username = username,password = password)

        if user:
            login(request, user)
            return HttpResponseRedirect("/eventsedit/")
        else:
            return HttpResponse('Wrong Login Credentials')
    else:
        return render(request, 'admin_login.html')
@login_required
def export_users_xls(request):
    if request.method == "POST":
        event_name = request.POST.get('event')
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="registrations.xls"'

        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Users Data') # this will make a sheet named Users Data

        # Sheet header, first row
        row_num = 0

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        columns = ['Timestamp','Participant Id','Name', 'Email', 'Contact No','Cost','Link', 'Referral', 'Coupon', 'Paid', 'Transaction Id']

        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style) # at 0 row 0 column

        # Sheet body, remaining rows
        font_style = xlwt.XFStyle()

        rows = registration.objects.filter(event = event_name).values_list('timestamp','participant_id','name', 'email', 'number','cost', 'link', 'referral','coupon', 'paid', 'transaction_id')
        for row in rows:
            row_num += 1
            for col_num in range(len(row)):
                if col_num == 0:
                    ws.write(row_num, col_num, str(row[col_num]), font_style)
                else:
                    ws.write(row_num, col_num, row[col_num], font_style)

        wb.save(response)
        return response
    else:
        return HttpResponse('Not Allowed')


def email_test(request):
    all_events = events.objects.all()
    return render(request, 'email_test.html', {'all_events' : all_events})

def send_email(request, event_name):
    event = events.objects.get(name = event_name)
    yag = yagmail.SMTP(user=event.email, password=event.password)
    yag.send(
        to='kcdeepak16@gmail.com',
        subject= " Registration",
        contents="Test successful"
    )
    return HttpResponse("Test successful")




# def event_management_login(request):
#     if request.method == "POST":
#         username = request.POST.get('username')
#         password = request.POST.get('password')
#         user = authenticate(username = username,password = password)
#         if user is not None:
#             login(request, user)
#             return render(request, 'event_edit.html')
#         else:
#             return HttpResponse('Wrong Login Credentials')
#     else:
#         return render(request, 'evt_management_login.html')


# after updating it will redirect to event detail_View
@login_required
def detail_view(request, id):
    obj = events.objects.get(id = id)
    if obj.eventadmin == request.user:
        context ={}
        context["data"] = obj
        return render(request, "evt_detail_view.html", context)
    else:
        return HttpResponse("Unauthorized")

# update view for events form
@login_required
def update_view(request, id):
    user = request.user
    print(user.username)
    context ={}
    obj = get_object_or_404(events, id = id)
    if obj.eventadmin == user:
        form = eventsForm(request.POST or None,request.FILES or None, instance = obj)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect("/eventsedit/"+id)
        context["form"] = form
        return render(request, "evt_update_view.html", context)
    else:
        return HttpResponse("Unauthorized")

# create view for event form
@login_required
def create_view(request):
    context ={}
    user = request.user
    form = eventsForm(request.POST or None,request.FILES or None)
    if form.is_valid():
        instance = form.save()
        instance.eventadmin = user
        instance.save()
        return HttpResponseRedirect('/eventsedit/'+str(instance.id))
    context['form']= form
    return render(request, "evt_create_view.html", context)

from django.views.generic.list import ListView
class EventsList(ListView):
	template_name = 'events_list.html'
	model = events
	context_object_name = 'object_list'


