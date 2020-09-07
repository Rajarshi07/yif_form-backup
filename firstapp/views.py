from django.shortcuts import render
from forms.form1 import form_registrations
from .models import events, registration, date_revenue, society_leads, state_connection
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
import pytz
# Create your views here.

def index(request):
    return render(request, 'index.html')

def other_states(request):
    if request.method == "POST":
        state_name = request.POST.get('state_select')
        print(state_name)
        state_con = state_connection.objects.get(state_name = state_name)
        print(state_con.state_connected_to)
        return event_page(request, state_con.state_connected_to)
    states = state_connection.objects.all()
    return render(request, 'other_states.html', {'states' : states})

def event_page(request, state):
    if '_' in state:
        state = state.replace('_', ' ')
    all_events = events.objects.filter(select_state = state)
    print(all_events)
    return render(request, 'events.html', { 'all_events' : all_events })

def event_details(request, event_name):
    current_event = events.objects.get(name = event_name)
    print(current_event.picture.url)
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
            cr = registration(name = name, email = email, number = number, link = link, event = event, cost = cost)
            cr.save()

            param_dict = {

                'MID': 'laGBhc85506378522813',
                'ORDER_ID': str(cr.id),
                'TXN_AMOUNT': str(cr.cost),
                'CUST_ID': str(cr.email),
                'INDUSTRY_TYPE_ID': 'Retail',
                'WEBSITE': 'WEBSTAGING',
                'CHANNEL_ID': 'WEB',
                'CALLBACK_URL': 'http://www.youthindiaevents.com/paytm_gateway/',
            }
            param_dict['CHECKSUMHASH'] = checksum.generate_checksum(param_dict, 'Uga@WGMhXmW_ta%&')
            return render(request, 'paytm.html', {'param_dict' : param_dict} )
        else:
            current_event = events.objects.get(name=event_name)
            return render(request, 'form.html',
                          {'form': current_registration, 'event_name': current_event.name, 'event_cost': current_event.cost})
    current_event = events.objects.get(name = event_name)
    intital_dict = {'event' : current_event.name, 'cost' : current_event.cost}
    form = form_registrations(initial = intital_dict)
    return render(request, 'form.html',{ 'form' : form, 'event_name': current_event.name,'event_cost': current_event.cost})

@csrf_exempt
def paytm_gateway(request):
    MERCHANT_KEY = 'Uga@WGMhXmW_ta%&'
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
            print('order successful')
            event_registered = events.objects.get(name = paid_registration.event)
            current_date_revenue = date_revenue.objects.filter(event_key = event_registered.id, day = datetime.today().date())
            if not paid_registration.paid:
                if not current_date_revenue:
                    new_date_revenue = date_revenue()
                    new_date_revenue.event_key = events.objects.get(name = paid_registration.event)
                    new_date_revenue.day = datetime.today().date()
                    new_date_revenue.no_of_participants = 1
                    new_date_revenue.revenue = int(paid_registration.cost)
                    print('new_date_revenue created')
                    new_date_revenue.save()
                else:
                    current_date_revenue[0].no_of_participants += 1
                    current_date_revenue[0].revenue += int(paid_registration.cost)
                    current_date_revenue[0].save()
                    print('new_cost_updated')
            paid_registration.paid = True
            paid_registration.save()
            port = 587  # For starttls
            smtp_server = "smtp.gmail.com"
            sender_email = event_registered.email
            receiver_email = paid_registration.email
            password = event_registered.password
            message = MIMEMultipart("alternative")
            message["Subject"] = paid_registration.event + " Registration"
            message["From"] = sender_email
            message["To"] = receiver_email
            message['Subject'] = paid_registration.event

            text = "Hey, {name}\nYou have been registered for {event_name}.\nYour participant ID is: {participant_id}.\n"

            text = text.format(name = paid_registration.name,event_name = paid_registration.event, participant_id = paid_registration.participant_id)

            message.attach(MIMEText(text, "plain"))

            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_server, port) as server:
                server.ehlo()  # Can be omitted
                server.starttls(context=context)
                server.ehlo()  # Can be omitted
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, message.as_string())
            state = events.objects.get(name = paid_registration.event).select_state
            return render(request, 'paytm_status.html', {'result' : True, 'details': paid_registration, 'state':state})
        else:
            state = events.objects.get(name=paid_registration.event).select_state
            return render(request, 'paytm_status.html', {'result' : False,  'state':state})
            print('order was not successful because' + response_dict['RESPMSG'])
    print(response_dict)
    return HttpResponse('Payment Successful')

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
                print(total_revenue, total_participants)
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
            if user.is_active and user.is_staff:
                all_events = events.objects.all()
                revenue = {}
                total = [0,0]
                for i in all_events:
                    revenue[i.name] = []
                    date_revenues = date_revenue.objects.filter(event_key=i.id)
                    total_revenue = 0
                    total_participants = 0
                    for j in date_revenues:
                        total_revenue += j.revenue
                        total_participants += j.no_of_participants
                    total[0] += total_revenue
                    total[1] += total_participants
                    revenue[i.name].append(total_revenue)
                    revenue[i.name].append(total_participants)
                return render(request, 'event_logs.html', {'details' : revenue, 'total_revenue' : total[0],
                                                           'total_participants' : total[1]})
            else:
                return HttpResponse('Wrong Login Credentials')
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

        columns = ['Timestamp','Name', 'Email', 'Contact No', 'Link']

        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style) # at 0 row 0 column

        # Sheet body, remaining rows
        font_style = xlwt.XFStyle()

        rows = registration.objects.filter(event = event_name, paid = True).values_list('timestamp','name', 'email', 'number', 'link')
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

