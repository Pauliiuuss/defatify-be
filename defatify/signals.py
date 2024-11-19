from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, WeightStat, BattleStatistic, Battle, BattleInvitation
from django.utils import timezone
from datetime import timedelta

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

@receiver(post_save, sender=WeightStat)
def update_battle_statistic(sender, instance, created, **kwargs):
    if created:
        # Get all in-progress battles for this user
        active_battles = BattleStatistic.objects.filter(user=instance.user, battle__status='in_progress')

        for battle_stat in active_battles:
            if battle_stat.stat_type == 'weight' and instance.weight is not None:
                battle_stat.current_value = instance.weight
            elif battle_stat.stat_type == 'bmi' and instance.bmi is not None:
                battle_stat.current_value = instance.bmi
            elif battle_stat.stat_type == 'body_fat' and instance.body_fat is not None:
                battle_stat.current_value = instance.body_fat
            elif battle_stat.stat_type == 'muscle_mass' and instance.muscle_mass is not None:
                battle_stat.current_value = instance.muscle_mass
            elif battle_stat.stat_type == 'body_water' and instance.body_water is not None:
                battle_stat.current_value = instance.body_water
            elif battle_stat.stat_type == 'bone_mass' and instance.bone_mass is not None:
                battle_stat.current_value = instance.bone_mass

            # Save the updated BattleStatistic
            battle_stat.save()

@receiver(post_save, sender=WeightStat)
def check_battle_completion(sender, instance, **kwargs):
    user = instance.user
    battles = Battle.objects.filter(
        participants=user,
        status='in_progress'
    )

    for battle in battles:
        if battle.type == 'stat_goal':
            # Check if the user's current stat has reached or exceeded the goal
            current_value = getattr(instance, battle.weight_param)
            if current_value is not None and current_value >= battle.goal_value:
                battle.status = 'finished'
                battle.winner = user  # Set the user as the winner
                battle.save()
        
        elif battle.type == 'duration':
            # Check if the duration has expired
            end_date = battle.created_at + timedelta(days=battle.duration)
            if timezone.now() >= end_date:
                # Determine the winner based on the highest progress in the stat parameter
                top_stat = BattleStatistic.objects.filter(battle=battle).order_by('-current_value').first()
                if top_stat:
                    battle.winner = top_stat.user
                battle.status = 'finished'
                battle.save()

@receiver(post_save, sender=Battle)
def delete_invitations_on_battle_status_change(sender, instance, **kwargs):
    if instance.status in ['deleted', 'finished']:
        BattleInvitation.objects.filter(battle=instance).delete()