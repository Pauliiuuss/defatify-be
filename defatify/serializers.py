from rest_framework import serializers
from .models import Profile, WeightStat, FriendRequest, Friendship, Battle, BattleStatistic, BattleInvitation
from django.contrib.auth.models import User
from .utils import convert_kg_to_lb, convert_lb_to_kg

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['bio', 'date_of_birth', 'pronouns', 'unit_preference']

class WeightStatSerializer(serializers.ModelSerializer):
    bmi = serializers.DecimalField(max_digits=5, decimal_places=2)
    body_fat = serializers.DecimalField(max_digits=5, decimal_places=2)
    muscle_mass = serializers.DecimalField(max_digits=5, decimal_places=2)
    body_water = serializers.DecimalField(max_digits=5, decimal_places=2)
    bone_mass = serializers.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        model = WeightStat
        fields = ['id', 'date', 'weight', 'bmi', 'body_fat', 'muscle_mass', 'body_water', 'bone_mass']
        read_only_fields = ['date']

    def to_representation(self, instance):
        """Convert units in the response based on user's preference."""
        representation = super().to_representation(instance)
        
        # Convert weight to imperial if the user preference is imperial
        unit_preference = self.context['request'].user.profile.unit_preference
        if unit_preference == 'imperial' and instance.weight is not None:
            representation['weight'] = convert_kg_to_lb(instance.weight)
        
        return representation

class FriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendRequest
        fields = ['id', 'from_user', 'to_user', 'status', 'timestamp']
        read_only_fields = ['status', 'timestamp']

class FriendshipSerializer(serializers.ModelSerializer):
    friend_username = serializers.CharField(source='friend.username', read_only=True)

    class Meta:
        model = Friendship
        fields = ['id', 'friend', 'friend_username', 'created_at']

class UserSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class BattleSerializer(serializers.ModelSerializer):
    creator = serializers.ReadOnlyField(source='creator.username')
    participants = serializers.StringRelatedField(many=True, read_only=True)
    winner_id = serializers.ReadOnlyField(source='winner.id')
    winner_name = serializers.ReadOnlyField(source='winner.username')

    class Meta:
        model = Battle
        fields = [
            'id', 'name', 'description', 'creator', 'type', 'weight_param', 
            'goal_value', 'duration', 'is_private', 'status', 'created_at', 
            'participants', 'winner_id', 'winner_name'
        ]
        read_only_fields = ['status', 'created_at', 'participants', 'winner_id', 'winner_name']

    def to_representation(self, instance):
        """Convert goal_value based on user's unit preference."""
        representation = super().to_representation(instance)
        
        # Check the user's unit preference
        unit_preference = self.context['request'].user.profile.unit_preference

        # Convert goal_value to lbs if the user prefers imperial units
        if unit_preference == 'imperial' and instance.weight_param == 'weight':
            representation['goal_value'] = convert_kg_to_lb(instance.goal_value)
        elif unit_preference == 'metric' and instance.weight_param == 'weight':
            # Convert goal_value to kg if stored in lbs
            representation['goal_value'] = convert_lb_to_kg(instance.goal_value)

        return representation

class BattleStatisticSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    starting_value = serializers.SerializerMethodField()
    current_value = serializers.SerializerMethodField()

    class Meta:
        model = BattleStatistic
        fields = ['user', 'stat_type', 'starting_value', 'current_value']

    def get_starting_value(self, obj):
        unit_preference = self.context['request'].user.profile.unit_preference
        value = obj.starting_value
        if obj.stat_type == 'weight' and unit_preference == 'imperial':
            return convert_kg_to_lb(value)
        return value

    def get_current_value(self, obj):
        unit_preference = self.context['request'].user.profile.unit_preference
        value = obj.current_value
        if obj.stat_type == 'weight' and unit_preference == 'imperial':
            return convert_kg_to_lb(value)
        return value

class LeaderboardSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    progress = serializers.SerializerMethodField()
    starting_value = serializers.SerializerMethodField()
    current_value = serializers.SerializerMethodField()

    class Meta:
        model = BattleStatistic
        fields = ['user', 'stat_type', 'starting_value', 'current_value', 'progress']

    def get_starting_value(self, obj):
        unit_preference = self.context['request'].user.profile.unit_preference
        value = obj.starting_value
        if obj.stat_type == 'weight' and unit_preference == 'imperial':
            return convert_kg_to_lb(value)
        return value

    def get_current_value(self, obj):
        unit_preference = self.context['request'].user.profile.unit_preference
        value = obj.current_value
        if obj.stat_type == 'weight' and unit_preference == 'imperial':
            return convert_kg_to_lb(value)
        return value

    def get_progress(self, obj):
        unit_preference = self.context['request'].user.profile.unit_preference
        progress = obj.current_value - obj.starting_value
        if obj.stat_type == 'weight' and unit_preference == 'imperial':
            return convert_kg_to_lb(progress)
        return progress
    
class BattleInvitationSerializer(serializers.ModelSerializer):
    inviting_user = serializers.ReadOnlyField(source='inviting_user.username')
    battle_name = serializers.ReadOnlyField(source='battle.name')

    class Meta:
        model = BattleInvitation
        fields = ['id', 'battle', 'battle_name', 'invited_user', 'inviting_user', 'status', 'created_at']
        read_only_fields = ['status', 'created_at']