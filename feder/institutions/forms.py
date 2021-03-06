from atom.ext.crispy_forms.forms import SingleButtonMixin
from braces.forms import UserKwargModelFormMixin
from dal import autocomplete
from django import forms

from .models import Institution


class InstitutionForm(SingleButtonMixin, UserKwargModelFormMixin, forms.ModelForm):
    class Meta:
        model = Institution
        fields = ["name", "tags", "jst", "regon", "email"]
        widgets = {"jst": autocomplete.ModelSelect2(url="teryt:community-autocomplete")}
