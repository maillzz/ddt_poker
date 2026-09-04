# web/forms.py
from django import forms


class PokerTaskForm(forms.Form):
    hole_cards = forms.CharField(
        label="Карманные карты (2 шт через пробел, например: As Kh)",
        initial="As Kh",
        max_length=10,
    )
    community = forms.CharField(
        label="Борд (до 5 карт через пробел, например: 7c 5d 2h)",
        required=False,
        max_length=20,
    )
    opponents = forms.IntegerField(
        label="Число оппонентов (1-9)", initial=1, min_value=1, max_value=9
    )
    simulations = forms.IntegerField(
        label="Число симуляций (100 - 200 000)",
        initial=10000,
        min_value=100,
        max_value=200000,
    )
    seed = forms.IntegerField(label="Seed", required=False)

    def clean_hole_cards(self):
        cards = self.cleaned_data["hole_cards"].split()
        if len(cards) != 2:
            raise forms.ValidationError(
                "Требуется указать ровно 2 карманные карты."
            )
        return cards

    def clean_community(self):
        val = self.cleaned_data.get("community", "").strip()
        if not val:
            return []
        cards = val.split()
        if len(cards) > 5:
            raise forms.ValidationError("На борде не может быть более 5 карт.")
        return cards