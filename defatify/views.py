from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny
from django.contrib.auth.hashers import make_password
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.generics import RetrieveAPIView, UpdateAPIView, GenericAPIView
from .models import Profile, WeightStat, FriendRequest, Friendship, Battle, BattleStatistic, BattleInvitation
from .serializers import ProfileSerializer, WeightStatSerializer, FriendRequestSerializer, FriendshipSerializer, UserSearchSerializer, BattleSerializer, LeaderboardSerializer, BattleInvitationSerializer
from django.utils.dateparse import parse_date
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

# REGISTER
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        if username and password and email:
            if User.objects.filter(username=username).exists():
                return Response({'error': 'Username already taken'}, status=status.HTTP_400_BAD_REQUEST)
            elif User.objects.filter(email=email).exists():
                return Response({'error': 'Account already exists on this email'}, status=status.HTTP_400_BAD_REQUEST)
            user = User.objects.create(username=username, email=email, password=make_password(password))
            return Response({'status': 'User registered successfully'}, status=status.HTTP_201_CREATED)
        return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)

# LOGIN
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            return Response({'status': 'Login successful'}, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

# LOGOUT
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

# GET PROFILE
class GetProfileView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        return Profile.objects.get(user=self.request.user)
    
# UPDAATE PROFILE

class UpdateProfileView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        return Profile.objects.get(user=self.request.user)
    
# POST WEIGHTS
class WeightStatListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WeightStatSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = WeightStat.objects.filter(user=user)
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(date__gte=parse_date(start_date))
        if end_date:
            queryset = queryset.filter(date__lte=parse_date(end_date))
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

# Get friends list
class FriendsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FriendshipSerializer

    def get_queryset(self):
        return Friendship.objects.filter(user=self.request.user)

# Send friend request
class FriendRequestCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FriendRequestSerializer

    def post(self, request):
        to_user = User.objects.get(id=request.data['to_user'])
        friend_request, created = FriendRequest.objects.get_or_create(from_user=request.user, to_user=to_user)
        if not created:
            return Response({"detail": "Friend request already sent."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(FriendRequestSerializer(friend_request).data, status=status.HTTP_201_CREATED)

# Get received and sent friend requests
class FriendRequestListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FriendRequestSerializer

    def get_queryset(self):
        user = self.request.user
        return FriendRequest.objects.filter(to_user=user) | FriendRequest.objects.filter(from_user=user)

# Accept or reject friend request
class FriendRequestUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FriendRequestSerializer

    def put(self, request, pk, action):
        try:
            friend_request = FriendRequest.objects.get(id=pk, to_user=request.user, status='pending')
        except FriendRequest.DoesNotExist:
            return Response({"detail": "Friend request not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if action == 'accept':
            friend_request.status = 'accepted'
            Friendship.objects.create(user=request.user, friend=friend_request.from_user)
            Friendship.objects.create(user=friend_request.from_user, friend=request.user)
        elif action == 'reject':
            friend_request.status = 'rejected'
        
        friend_request.save()
        return Response(FriendRequestSerializer(friend_request).data)

# Remove friend
class RemoveFriendView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            friendship = Friendship.objects.get(user=request.user, friend_id=pk)
            Friendship.objects.filter(user=request.user, friend_id=pk).delete()
            Friendship.objects.filter(user_id=pk, friend=request.user).delete()
            return Response({"detail": "Friend removed."}, status=status.HTTP_204_NO_CONTENT)
        except Friendship.DoesNotExist:
            return Response({"detail": "Friendship not found."}, status=status.HTTP_404_NOT_FOUND)

# Search users by username
class UserSearchView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSearchSerializer

    def get_queryset(self):
        query = self.request.query_params.get('query', '')
        return User.objects.filter(username__icontains=query).exclude(id=self.request.user.id)
    
# Battles
    
# List and create battles
class BattleListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BattleSerializer

    def get_queryset(self):
        user = self.request.user
        return Battle.objects.filter(participants=user).distinct() | Battle.objects.filter(creator=user).distinct()

    def perform_create(self, serializer):
        # Create the battle and set the creator
        battle = serializer.save(creator=self.request.user)
        
        # Automatically add the creator as a participant
        battle.participants.add(self.request.user)
        
        # Retrieve the latest weight stat for the user to use as the starting value
        latest_weight_stat = WeightStat.objects.filter(user=self.request.user).order_by('-date').first()

        # Initialize the BattleStatistic for the creator with their current stats
        if latest_weight_stat:
            BattleStatistic.objects.create(
                battle=battle,
                user=self.request.user,
                stat_type=battle.weight_param,
                starting_value=getattr(latest_weight_stat, battle.weight_param, None),
                current_value=getattr(latest_weight_stat, battle.weight_param, None)
            )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
# Start Battle
class StartBattleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        battle = get_object_or_404(Battle, id=pk)

        # Check if the authenticated user is the creator of the battle
        if battle.creator != request.user:
            return Response({"detail": "You do not have permission to start this battle."},
                            status=status.HTTP_403_FORBIDDEN)

        # Check if the battle is in "not_started" status
        if battle.status != 'not_started':
            return Response({"detail": "Battle has already started or finished."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Update the battle status to "in_progress"
        battle.status = 'in_progress'
        battle.save()
        return Response({"detail": "Battle started successfully.", "status": battle.status},
                        status=status.HTTP_200_OK)

# Get details of a specific battle
class BattleDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BattleSerializer
    queryset = Battle.objects.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

#Join a battle
class BattleJoinView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        battle = get_object_or_404(Battle, id=pk)

        # Check if the battle is already finished
        if battle.status == 'finished':
            return Response({"detail": "This battle has finished."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Prevent joining private battles through this endpoint
        if battle.is_private:
            return Response({"detail": "You cannot join a private battle directly. Accept the invitation to join."}, status=status.HTTP_403_FORBIDDEN)

        # Fetch the user's latest weight or relevant stat as the starting value
        user_stat = WeightStat.objects.filter(user=request.user).order_by('-date').first()
        
        # Set starting value to the user's latest stat, or default to 0 if no record exists
        starting_value = user_stat.weight if user_stat and battle.weight_param == 'weight' else 0
        # You can add similar checks for other stat types if required

        # Add the user to the battle participants
        battle.participants.add(request.user)

        # Initialize BattleStatistic for the user
        BattleStatistic.objects.create(
            battle=battle,
            user=request.user,
            stat_type=battle.weight_param,
            starting_value=starting_value,
            current_value=starting_value
        )

        return Response({"detail": "Joined the battle."}, status=status.HTTP_200_OK)

# Leave a battle
class BattleLeaveView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        battle = get_object_or_404(Battle, id=pk, participants=request.user)
        battle.participants.remove(request.user)
        BattleStatistic.objects.filter(battle=battle, user=request.user).delete()
        return Response({"detail": "Left the battle."}, status=status.HTTP_204_NO_CONTENT)

# Leaderboard for a specific battle
class BattleLeaderboardView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LeaderboardSerializer

    def get_queryset(self):
        battle = get_object_or_404(Battle, id=self.kwargs['pk'])
        return BattleStatistic.objects.filter(battle=battle)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
# Send an invitation to join a battle
class BattleInviteView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BattleInvitationSerializer

    def post(self, request, pk):
        battle = get_object_or_404(Battle, id=pk)
        invited_user_id = request.data.get('invited_user')
        invited_user = get_object_or_404(User, id=invited_user_id)

        # Check if the invited user is the same as the inviter
        if invited_user == request.user:
            return Response({"detail": "You cannot send an invitation to yourself."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the invited user is already a participant
        if battle.participants.filter(id=invited_user.id).exists():
            return Response({"detail": "This user is already a participant in the battle."}, status=status.HTTP_400_BAD_REQUEST)

        if BattleInvitation.objects.filter(battle=battle, invited_user=invited_user, status='pending').exists():
            return Response({"detail": "An invitation is already pending for this user."}, status=status.HTTP_400_BAD_REQUEST)

        invitation = BattleInvitation.objects.create(
            battle=battle,
            invited_user=invited_user,
            inviting_user=request.user
        )
        return Response(BattleInvitationSerializer(invitation).data, status=status.HTTP_201_CREATED)

# Accept an invitation
class AcceptBattleInvitationView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, invitation_id):
        # Get the invitation, ensuring it's for the requesting user and is still pending
        invitation = get_object_or_404(BattleInvitation, id=invitation_id, invited_user=request.user, status='pending')
        
        # Mark the invitation as accepted
        invitation.status = 'accepted'
        invitation.save()

        # Add the user to the battle participants
        battle = invitation.battle
        battle.participants.add(request.user)

        # Initialize BattleStatistic for the user with their latest stats
        latest_weight_stat = WeightStat.objects.filter(user=request.user).order_by('-date').first()
        if latest_weight_stat:
            BattleStatistic.objects.create(
                battle=battle,
                user=request.user,
                stat_type=battle.weight_param,
                starting_value=getattr(latest_weight_stat, battle.weight_param, None),
                current_value=getattr(latest_weight_stat, battle.weight_param, None)
            )

        return Response({"detail": "Invitation accepted and joined the battle."}, status=status.HTTP_200_OK)

# Reject an invitation
class RejectBattleInvitationView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, invitation_id):
        invitation = get_object_or_404(BattleInvitation, id=invitation_id, invited_user=request.user, status='pending')
        invitation.status = 'rejected'
        invitation.save()
        return Response({"detail": "Invitation rejected."}, status=status.HTTP_200_OK)

# List pending invitations for the authenticated user
class PendingBattleInvitationsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BattleInvitationSerializer

    def get_queryset(self):
        return BattleInvitation.objects.filter(invited_user=self.request.user, status='pending')