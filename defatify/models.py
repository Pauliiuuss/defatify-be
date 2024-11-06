from django.db import models
from django.contrib.auth.models import User

# PROFILE MODEL
class Profile(models.Model):
    UNIT_CHOICES = [
        ('metric', 'Metric'),
        ('imperial', 'Imperial'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    pronouns = models.CharField(max_length=50, blank=True, null=True)
    unit_preference = models.CharField(max_length=10, choices=UNIT_CHOICES, default='metric')

    def __str__(self):
        return self.user.username

# WEIGHTS MODEL
# class WeightStat(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weight_stats')
#     date = models.DateTimeField(auto_now_add=True)  # Automatically set to current date and time
#     weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
#     bmi = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
#     body_fat = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
#     muscle_mass = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
#     body_water = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
#     bone_mass = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

#     def __str__(self):
#         return f"{self.user.username} - {self.date}"
class WeightStat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weight_stats')
    date = models.DateTimeField(auto_now_add=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    bmi = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    body_fat = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    muscle_mass = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    body_water = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    bone_mass = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Update BattleStatistic starting_value for not_started battles
        from .models import BattleStatistic, Battle  # Avoid circular imports

        # Retrieve battles where the user is participating and the status is "not_started"
        battles = Battle.objects.filter(participants=self.user, status='not_started')
        
        # Loop through each battle and update the starting value in BattleStatistic
        for battle in battles:
            battle_stat, created = BattleStatistic.objects.get_or_create(
                battle=battle,
                user=self.user,
                stat_type=battle.weight_param  # Ensure this matches the weight param type
            )
            # Update the starting value based on the latest weight stat for the relevant parameter
            setattr(battle_stat, 'starting_value', getattr(self, battle.weight_param, None))
            setattr(battle_stat, 'current_value', getattr(self, battle.weight_param, None))
            battle_stat.save()

    def __str__(self):
        return f"{self.user.username} - {self.date}"
    
# FRIENDS MODEL
class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, related_name='sent_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='received_requests', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], default='pending')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.status})"

class Friendship(models.Model):
    user = models.ForeignKey(User, related_name='friends', on_delete=models.CASCADE)
    friend = models.ForeignKey(User, related_name='_friends', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} & {self.friend.username}"
    
# BATTLES MODEL
class Battle(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('finished', 'Finished')
    ]

    TYPE_CHOICES = [
        ('stat_goal', 'Stat Goal'),
        ('duration', 'Duration')
    ]

    PARAM_CHOICES = [
        ('weight', 'Weight'),
        ('body_fat', 'Body Fat'),
        ('muscle_mass', 'Muscle Mass')
        # Add other parameters as needed
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    creator = models.ForeignKey(User, related_name="created_battles", on_delete=models.CASCADE)
    participants = models.ManyToManyField(User, related_name="battles", blank=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)  # "stat_goal" or "duration"
    weight_param = models.CharField(max_length=20, choices=PARAM_CHOICES)
    goal_value = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)  # For stat goal type
    duration = models.IntegerField(blank=True, null=True)  # In days, for duration type
    is_private = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    created_at = models.DateTimeField(auto_now_add=True)
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_battles')

    def __str__(self):
        return self.name
    
class BattleStatistic(models.Model):
    battle = models.ForeignKey(Battle, on_delete=models.CASCADE, related_name="statistics")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stat_type = models.CharField(max_length=20)  # E.g., "weight"
    starting_value = models.DecimalField(max_digits=5, decimal_places=2)
    current_value = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.user.username} - {self.stat_type} in {self.battle.name}"
    
class BattleInvitation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ]

    battle = models.ForeignKey(Battle, on_delete=models.CASCADE, related_name="invitations")
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="battle_invitations")
    inviting_user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invitation for {self.invited_user.username} to join {self.battle.name}"