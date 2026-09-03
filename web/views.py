from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from web import services
from web.models import PokerHand


@login_required
def hand_list(request):
    hands = PokerHand.objects.filter(owner=request.user)[:50]

    return render(
        request,
        "web/hand_list.html",
        {"hands": hands},
    )


@login_required
def hand_create(request):
    if request.method == "POST":
        players_count = int(request.POST.get("players_count", 2))
        pot_size = request.POST.get("pot_size", "0")
        call_amount = request.POST.get("call_amount", "0")

        hand = services.create_hand(
            owner=request.user,
            players_count=players_count,
            pot_size=pot_size,
            call_amount=call_amount,
        )

        return redirect("hand_detail", pk=hand.pk)

    return render(request, "web/hand_form.html")


@login_required
def hand_detail(request, pk: int):
    hand = get_object_or_404(
        PokerHand,
        pk=pk,
        owner=request.user,
    )

    return render(
        request,
        "web/hand_detail.html",
        {"hand": hand},
    )