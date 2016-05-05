from django.contrib.auth.models import User
from django.db import models


class Stadium(models.Model):
    SURFACE_CHOICES = [
        ('CLAY', 'Clay Court'),
        ('HARD', 'Hard Court'),
    ]
    surface_choice = models.CharField(max_length=4, choices=SURFACE_CHOICES, default='HARD')
    location_name = models.CharField(max_length=20)

    def __unicode__(self):
        return unicode(self.location_name) + " - " + unicode(self.surface_choice)


class Player(models.Model):
    """Model used to track a specific player. Extends user with a one to one field."""
    user = models.OneToOneField(User, default=0)
    game_wins = models.IntegerField(default=0)
    game_losses = models.IntegerField(default=0)
    match_wins = models.IntegerField(default=0)
    match_losses = models.IntegerField(default=0)
    point = models.IntegerField(default=0)

    def get_name(self):
        return self.user.get_username()

    def __unicode__(self):
        return self.get_name()

    def game_win_percent(self):
        if self.game_wins + self.game_losses == 0:
            return "N/A"
        return '{:.2%}'.format(float(self.game_wins) / float(self.game_wins + self.game_losses))

    def match_win_percent(self):
        if self.match_wins + self.match_losses == 0:
            return "N/A"
        return '{:.2%}'.format(float(self.match_wins) / float(self.match_wins + self.match_losses))


class Match(models.Model):
    TYPE_CHOICES = [
        ('SINGLES', 'Singles Match'),
        ('DOUBLES', 'Doubles Match'),
    ]
    type_choice = models.CharField(max_length=7, choices=TYPE_CHOICES, default='SINGLES', blank=True, null=True)

    match_date = models.DateField()
    stadium = models.ForeignKey(Stadium)

    winner1 = models.ForeignKey(Player, related_name="match_winning_player")
    winner2 = models.ForeignKey(Player, related_name="match_winning_player2", blank=True, null=True)
    loser1 = models.ForeignKey(Player, related_name="match_losing_player")
    loser2 = models.ForeignKey(Player, related_name="match_losing_player2", blank=True, null=True)

    winner_games = models.PositiveIntegerField(default=0)
    loser_games = models.PositiveIntegerField(default=0)

    def isSinglesType(self):
        if self.type_choice == 'SINGLES':
            return True
        else:
            return False

    def __unicode__(self):
        if self.type_choice == 'SINGLES':
            return u'%s (W %s) vs. %s (L %s)' % \
                   (self.winner1, self.winner_games, self.loser1, self.loser_games)
        else:
            return u'%s, %s (W %s) vs. %s, %s (L %s)' % \
                   (self.winner1, self.winner2, self.winner_games, self.loser1,
                    self.loser2, self.loser_games)
