from rest_framework.mixins import ListModelMixin
from rest_framework.filters import BaseFilterBackend

from django_elasticsearch.models import EsIndexable


class ElasticsearchFilterBackend(BaseFilterBackend):
    search_param = 'q'

    def filter_queryset(self, request, queryset, view):
        model = queryset.model

        if view.action == 'list':
            if not issubclass(model, EsIndexable):
                raise ValueError("Model %s is not indexed in Elasticsearch. Make it indexable by subclassing django_elasticsearch.models.EsIndexable." % model)

            query = request.QUERY_PARAMS.get(self.search_param, '')
            ordering = getattr(view, 'ordering', getattr(model.Meta, 'ordering', None))
            filterable = getattr(view, 'filter_fields', [])
            filters = dict([(k, v) for k, v in request.GET.iteritems() if k in filterable])
            q = model.es.search(query).filter(**filters)
            if ordering:
                q.order_by(*ordering)

            return q
        else:
            return queryset


class FacetedListModelMixin(ListModelMixin):
    """
    Add faceted info to the response in case the ElasticsearchFilterBackend was used.
    """
    filter_backends = [ElasticsearchFilterBackend,]

    def list(self, request, *args, **kwargs):
        r = super(FacetedListModelMixin, self).list(request, *args, **kwargs)
        # Injecting the facets in the response if the FilterBackend was used.

        if getattr(self.queryset, 'facets', None):
            r.data['facets'] = self.queryset.facets
        return r