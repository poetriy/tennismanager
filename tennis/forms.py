from __future__ import unicode_literals

from django.forms import ModelForm, DateInput

from tennis.models import Match


class MatchForm(ModelForm):
    class Meta:
        model = Match
        exclude = ()
        widgets = {
            'match_date': DateInput(attrs={'class': 'datepicker'}),
        }
