from django.contrib.auth.models import User

from rest_framework import permissions

from authentication.models import UserProfile

class site_manager_only(permissions.BasePermission):
	def has_permission(self,request,view):
		try:
			user_profile = UserProfile.objects.get(user=request.user)
			return user_profile.site_manager
		except TypeError:
			return False