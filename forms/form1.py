from django import forms
from firstapp.models import registration
from django.core.validators import MinLengthValidator

class form_registrations(forms.Form):
    """def __init__(self, *args, **kwargs):
        super(form_registrations, self).__init__(*args, **kwargs)
        self.fields["number"].min_length = 10
        self.fields["number"].validators.append(MinLengthValidator)
        print(self.fields['number'].validators)
    class Meta():
        model = registration
        fields = ('name', 'email','number', 'link', 'event', 'cost')
        widgets = {'event': forms.HiddenInput(), 'cost': forms.HiddenInput()}"""
    name = forms.CharField(label = "Name", max_length=50)
    email = forms.EmailField(label="Email", max_length=50,  error_messages={'invalid': 'Incorrect Email Address'})
    number = forms.CharField(label="Number", min_length=10, validators=[MinLengthValidator(10)],
                             error_messages={'min_length': ('Ensure the number has at least 10 digits')})
    link = forms.CharField(label="Link (If Any)", max_length = 50, required =  False)
    referral = forms.CharField(label = "Referral (If Any)", max_length = 100,required = False)
    coupon = forms.CharField(label = "Transaction Id (Last 5 digits)", max_length=100)
    event = forms.CharField(label="Event", max_length=50, widget= forms.HiddenInput())
    cost = forms.CharField(label="Cost", max_length=50, widget= forms.HiddenInput())




