from django import forms 
from .models import events
  
  
# creating a form 
class eventsForm(forms.ModelForm): 
  
    # create meta class 
    class Meta: 
        # specify model to be used 
        model = events
  
        # specify fields to be used 
        fields = ["name","select_state","cluster","summary","picture","rules","cost","start_day","group_event"] 
