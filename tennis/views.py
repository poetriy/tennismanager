import re

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, render_to_response
from django.template import RequestContext

from tennis.forms import MatchForm
from tennis.models import Player, Match


def is_valid_entry(entry):
    """Returns if a given entry is a valid input"""
    return entry and 30 >= len(entry) >= 1 and re.match('^[A-Za-z\-_@0-9.\']*$', entry)


def is_valid_user(info):
    """Returns if a given user_creation info is valid. If not, gives an appropriate message alongside"""
    if not is_valid_entry(info['username']):
        return False, "Please enter a valid username"
    if User.objects.filter(username=info['username']):
        return False, "Username taken, please select another"
    if not is_valid_entry(info['email']): return False, "Please enter a valid e-mail"
    if User.objects.filter(username=info['email']):
        return False, "Email already in use"
    if not is_valid_entry(info['password']): return False, "Please enter a valid password"
    if not is_valid_entry(info['confirm_password']):
        return False, "Please confirm your password"
    if not (info['password'] == info['confirm_password']):
        return False, "Your passwords did not match."
    return True, ""


def standings(request):
    """View to send standings data based on template in tennis/standings.html"""
    players = Player.objects.order_by('-point')
    return render(request, 'tennis/standings.html', {'players': players})


def history(request):
    """View to send history data based on template in tennis/history.html"""
    matches = Match.objects.order_by('-match_date')
    return render(request, 'tennis/history.html', {'matches': matches})


def delete_history(request, match_id):
    delete_match = get_object_or_404(Match, pk=match_id)

    winner1 = get_object_or_404(Player, pk=delete_match.winner1.id)
    loser1 = get_object_or_404(Player, pk=delete_match.loser1.id)

    winner1.match_wins -= 1
    winner1.game_wins -= delete_match.winner_games
    winner1.game_losses -= delete_match.loser_games
    winner1.point = winner1.game_wins - winner1.game_losses

    loser1.match_losses -= 1
    loser1.game_wins -= delete_match.loser_games
    loser1.game_losses -= delete_match.winner_games
    loser1.point = loser1.game_wins - loser1.game_losses

    winner1.save()
    loser1.save()

    if not (delete_match.winner2 is None or delete_match.loser2 is None):
        winner2 = get_object_or_404(Player, pk=delete_match.winner2.id)
        loser2 = get_object_or_404(Player, pk=delete_match.loser2.id)
        winner2.match_wins -= 1
        winner2.game_wins -= delete_match.winner_games
        winner2.game_losses -= delete_match.loser_games
        winner2.point = winner2.game_wins - winner2.game_losses

        loser2.match_losses -= 1
        loser2.game_wins -= delete_match.loser_games
        loser2.game_losses -= delete_match.winner_games
        loser2.point = loser2.game_wins - loser2.game_losses

        winner2.save()
        loser2.save()

    delete_match.delete()

    return HttpResponseRedirect(reverse('standings'))


def player_details(request, player_id):
    """View to send player data corresponding to player_id to page with template in tennis/player_details.html"""
    p = get_object_or_404(Player, pk=player_id)
    player_matches = Match.objects.filter(winner1=player_id) | Match.objects.filter(loser1=player_id) \
                     | Match.objects.filter(winner2=player_id) | Match.objects.filter(loser2=player_id)
    player_matches = player_matches.order_by('-match_date')
    """ Make the list of matches a list of tuples.
      The first entry is a boolean stating if player corresponding to player_id won.
      The second entry is the match un-altered."""
    player_matches = map((lambda x:
                          (x.winner1.id == int(player_id) or x.winner2.id == int(player_id)
                           if x.winner2 is not None else (x.winner1.id == int(player_id)), x)),
                         player_matches)
    return render(request, 'tennis/player_details.html',
                  {'player': p, 'matches': player_matches})


def register(request):
    """Page to allow registration from user, using generic RegisterForm from django's library"""

    registered = False

    if request.method == 'POST':
        info = {"username": request.POST['username'].lower(), "email": request.POST['email'],
                "password": request.POST['password'],
                "confirm_password": request.POST['confirm_password']}
        processed_info = is_valid_user(info)
        if processed_info[0]:
            new_user = User.objects.create_superuser(username=info['username'], email=info['email'],
                                                     password=info['password'])
            new_user.save()

            player = Player(user=new_user)
            player.save()

            registered = True
        else:
            messages.error(request, processed_info[1])

    return render(request, 'tennis/register.html', {'registered': registered})


def user_login(request):
    """Page to allow logging in"""
    context = RequestContext(request)

    if request.method == 'POST':
        username = request.POST['username'].lower()
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request, user)
                messages.success(request, "Welcome to the Tennis Manager, " + user.get_username())
                return HttpResponseRedirect(reverse('standings'))
            else:
                messages.error(request, "This account is disabled, try again.")
                return render(request, 'tennis/login.html')
        else:
            messages.error(request, "Either your username or password is incorrect. Try again.")
            return render(request, 'tennis/login.html')
    else:
        return render_to_response('tennis/login.html', {}, context)


@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('standings'))


@login_required
def report(request):
    return render(request, 'tennis/report.html')


@login_required
def report_singles(request):
    edit_form = MatchForm()
    edit_form.type_choice = 'SINGLES'
    return render(request, 'tennis/report_singles.html', {'form': edit_form})


@login_required
def report_doubles(request):
    edit_form = MatchForm()
    return render(request, 'tennis/report_doubles.html', {'form': edit_form})


@login_required
def make_singles(request):
    if request.user.is_authenticated():
        result_form = MatchForm(request.POST)
        if result_form.is_valid():
            winner1_id = result_form.cleaned_data['winner1'].id
            loser1_id = result_form.cleaned_data['loser1'].id
            date = result_form.cleaned_data['match_date']
            winner_game = result_form.cleaned_data['winner_games']
            loser_game = result_form.cleaned_data['loser_games']
            stadium = result_form.cleaned_data['stadium']
            if winner1_id == loser1_id:
                messages.error(request, "You selected the same person to win and lose. Try again.")
                return report_singles(request)
            elif winner_game == 0:
                messages.error(request, "You selected winner game 0. Try again.")
                return report_singles(request)
            elif winner_game <= loser_game:
                messages.error(request, "Winner game is smaller than loser game. Try again.")
                return report_singles(request)
            else:
                winner = get_object_or_404(Player, pk=winner1_id)
                loser = get_object_or_404(Player, pk=loser1_id)
                if not (winner.user == request.user or loser.user == request.user):
                    messages.error(request, "You can only report a match that you are involved in.")
                    return report_singles(request)
                else:
                    winner.match_wins += 1
                    winner.game_wins += winner_game
                    winner.game_losses += loser_game
                    winner.point = winner.game_wins - winner.game_losses

                    loser.match_losses += 1
                    loser.game_wins += loser_game
                    loser.game_losses += winner_game
                    loser.point = loser.game_wins - loser.game_losses

                    match = Match(match_date=date,
                                  winner1=winner,
                                  loser1=loser,
                                  winner_games=winner_game,
                                  loser_games=loser_game,
                                  stadium=stadium,
                                  type_choice='SINGLES'
                                  )

                    loser.save()
                    winner.save()
                    match.save()

                    messages.success(request, "Submission successful!")
                    return HttpResponseRedirect(reverse('standings'))
        else:
            messages.error(request, result_form.errors)
            return report_singles(request)

    else:
        messages.error(request, "You must be logged in to report a match.")
        return report_singles(request)


@login_required
def make_doubles(request):
    if request.user.is_authenticated():
        result_form = MatchForm(request.POST)
        result_form.fields['winner2'].required = True
        result_form.fields['loser2'].required = True
        if result_form.is_valid():
            winner1_id = result_form.cleaned_data['winner1'].id
            winner2_id = result_form.cleaned_data['winner2'].id
            loser1_id = result_form.cleaned_data['loser1'].id
            loser2_id = result_form.cleaned_data['loser2'].id
            date = result_form.cleaned_data['match_date']
            winner_game = result_form.cleaned_data['winner_games']
            loser_game = result_form.cleaned_data['loser_games']
            stadium = result_form.cleaned_data['stadium']
            if winner1_id == loser1_id or winner1_id == loser2_id \
                    or winner2_id == loser1_id or winner2_id == loser2_id:
                messages.error(request, "You selected the same person to win and lose. Try again.")
                return report_doubles(request)
            elif winner1_id == winner2_id:
                messages.error(request, "You selected the same person to win. Try again.")
                return report_doubles(request)
            elif loser1_id == loser2_id:
                messages.error(request, "You selected the same person to lose. Try again.")
                return report_doubles(request)
            elif winner_game == 0:
                messages.error(request, "You selected winner game 0. Try again.")
                return report_doubles(request)
            elif winner_game <= loser_game:
                messages.error(request, "Winner game is smaller than loser game. Try again.")
                return report_doubles(request)
            else:
                winner1 = get_object_or_404(Player, pk=winner1_id)
                winner2 = get_object_or_404(Player, pk=winner2_id)
                loser1 = get_object_or_404(Player, pk=loser1_id)
                loser2 = get_object_or_404(Player, pk=loser2_id)
                if not (winner1.user == request.user or loser1.user == request.user \
                                or winner2.user == request.user or loser2.user == request.user):
                    messages.error(request, "You can only report a match that you are involved in.")
                    return report_doubles(request)
                else:
                    winner1.match_wins += 1
                    winner1.game_wins += winner_game
                    winner1.game_losses += loser_game
                    winner1.point = winner1.game_wins - winner1.game_losses

                    winner2.match_wins += 1
                    winner2.game_wins += winner_game
                    winner2.game_losses += loser_game
                    winner2.point = winner2.game_wins - winner2.game_losses

                    loser1.match_losses += 1
                    loser1.game_wins += loser_game
                    loser1.game_losses += winner_game
                    loser1.point = loser1.game_wins - loser1.game_losses

                    loser2.match_losses += 1
                    loser2.game_wins += loser_game
                    loser2.game_losses += winner_game
                    loser2.point = loser2.game_wins - loser2.game_losses

                    match = Match(match_date=date,
                                  winner1=winner1,
                                  winner2=winner2,
                                  loser1=loser1,
                                  loser2=loser2,
                                  winner_games=winner_game,
                                  loser_games=loser_game,
                                  stadium=stadium,
                                  type_choice='DOUBLES'
                                  )

                    winner1.save()
                    winner2.save()
                    loser1.save()
                    loser2.save()
                    match.save()

                    messages.success(request, "Submission successful!")
                    return HttpResponseRedirect(reverse('standings'))
        else:
            messages.error(request, result_form.errors)
            return report_doubles(request)

    else:
        messages.error(request, "You must be logged in to report a match.")
        return report_doubles(request)
