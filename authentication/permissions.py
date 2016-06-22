

class Allow_All(BasePermission):
	def has_permission(self,request,view):
		return True