from django import forms


class TaskForm(forms.Form):
    name = forms.CharField(
        label="Название",
        max_length=200,
    )

    hole_cards = forms.CharField(
        label="Карты игрока",
        initial="As Kh",
        help_text="Например: As Kh",
    )

    community_cards = forms.CharField(
        label="Карты стола",
        required=False,
        help_text="Например: 2c 7d Jc",
    )

    opponents = forms.IntegerField(
        label="Количество противников",
        initial=1,
        min_value=1,
        max_value=9,
    )

    pot = forms.FloatField(
        label="Размер банка",
        initial=0,
        min_value=0,
    )

    call_amount = forms.FloatField(
        label="Размер колла",
        initial=0,
        min_value=0,
    )

    simulations = forms.IntegerField(
        label="Количество симуляций",
        initial=10_000,
        min_value=100,
        max_value=1_000_000,
    )

    def params(self) -> dict:
        d = self.cleaned_data

        return {
            "hole_cards": d["hole_cards"].split(),
            "community_cards": d["community_cards"].split(),
            "opponents": d["opponents"],
            "pot": d["pot"],
            "call_amount": d["call_amount"],
            "simulations": d["simulations"],
        }