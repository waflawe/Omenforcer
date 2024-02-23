from rest_framework.permissions import IsAuthenticatedOrReadOnly


class TopicsOperationsPermission(IsAuthenticatedOrReadOnly):
    pass
