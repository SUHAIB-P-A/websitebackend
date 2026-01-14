# from rest_framework import serializers
# from .models import Message
# from formapp.models import Staff
# 
# class MessageSerializer(serializers.ModelSerializer):
#     sender_name = serializers.CharField(source='sender.name', read_only=True)
#     receiver_name = serializers.CharField(source='receiver.name', read_only=True)
#     sender_role = serializers.CharField(source='sender.role', read_only=True)
# 
#     class Meta:
#         model = Message
#         fields = '__all__'
# 
#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#         
#         if instance.is_revoked:
#             # Determine based on the request user context or logic
#             # Since we can't easily access request user in generic ModelSerializer without passing context,
#             # we will infer or rely on provided context keys?
#             # Actually, viewset passes 'request' in context.
#             user_id = self.context['request'].query_params.get('user1') or self.context['request'].query_params.get('user_id')
#             
#             # If user_id wasn't in params (e.g. create/update), try user.id
#             if not user_id and self.context['request'].user.is_authenticated:
#                  # Note: In adminwebsite context, we might be using session auth or passing user_id manually.
#                  # The 'conversation' view uses query params `user1` (usually current user).
#                  pass
#             
#             # Better Approach:
#             # We know the current viewer is usually 'user1' in conversation view or 'request.user'.
#             # Let's try to detect if the viewer is the sender.
#             
#             # Logic: If query param 'user1' matches sender, they are the sender. 
#             # OR we can return specific fields like 'is_sender_viewer' but that's complex.
#             
#             # Let's use the standard "You" logic if we can identify the viewer.
#             # In 'conversation' view: user1=viewer.
#             
#             viewer_id = self.context['request'].query_params.get('user1')
#             
#             # Fallback for other comparisons (string vs int)
#             is_sender = False
#             if viewer_id:
#                 is_sender = str(viewer_id) == str(instance.sender.id)
#             
#             if is_sender:
#                 data['content'] = "You deleted this message"
#             else:
#                 data['content'] = "This message was deleted"
#             
#             data['is_revoked_placeholder'] = True
#             
#         return data
