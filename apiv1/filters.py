from rest_framework import filters

from forum_app.constants import SearchParamsExpressions


class TopicsSearchFilter(filters.SearchFilter):
    def get_search_fields(self, view, request):
        search_fields = [f for p, f in SearchParamsExpressions.Params.items() if request.query_params.get(p)]
        if len(search_fields) > 0: return search_fields
        return super().get_search_fields(view, request)
