from django.contrib.admin.widgets import AutocompleteMixin
from django.urls import reverse

from .filters import MultiSelectRelatedFilter, RelatedDropdownFilter, RelatedOnlyDropdownFilter


class LazyAutocompleteListFilterMixin:
    """Avoid loading all related objects for AJAX-backed filters."""

    def field_choices(self, field, request, model_admin):
        # The autocomplete templates get their options over AJAX and only use
        # lookup_choices to decide whether the filter should be displayed.
        return ()

    def has_output(self):
        # RelatedFieldListFilter hides filters without lookup choices by
        # default, but autocomplete options are deliberately loaded lazily.
        return True


class BaseAutocompleteListFilter:
    template = "more_admin_filters/autocomplete_list_filter.html"

    def _get_app_label(self):
        return self.field.model._meta.app_label

    def _get_model_name(self):
        return self.field.model._meta.model_name

    def __init__(self, field, request, params, model, model_admin, *args, **kwargs):
        self.value = None

        super().__init__(field, request, params, model, model_admin, *args, **kwargs)

        self.app_label = model._meta.app_label
        self.model = model
        self.model_name = field.model._meta.model_name
        self.related_model = field.related_model
        self.related_app_label = field.related_model._meta.app_label
        self.related_model_name = field.related_model._meta.model_name
        self.request = request
        self.field_path = kwargs["field_path"]

    def queryset(self, request, queryset):
        value = self.used_parameters.get(f"{self.field_path}__id__exact")

        if not value:
            return queryset

        if isinstance(value, list):
            # in case of multiples, always assume the last value
            _value = value[-1]
        else:
            _value = value

        # assign value to self for use in choices
        self.value = _value

        try:
            return queryset.filter(**{self.field_path: _value})
        except ValueError:
            return queryset.none()

    def choices(self, changelist):
        autocomplete_url = reverse("admin:autocomplete")
        selected_item = None

        if self.value is not None:
            try:
                selected_item = self.field.related_model.objects.filter(id=self.value).first()
            except ValueError:
                selected_item = None

        return (
            {
                "app_label": self._get_app_label(),
                "model_name": self._get_model_name(),
                "field_name": self.field.name,
                "autocomplete_url": autocomplete_url,
                "selected_item": selected_item if selected_item else "",
            },
        )


class AutocompleteListFilter(BaseAutocompleteListFilter, RelatedDropdownFilter):
    pass


class AutocompleteOnlyListFilter(
    BaseAutocompleteListFilter,
    RelatedOnlyDropdownFilter,
):
    pass


class RelatedAutocompleteListFilter(AutocompleteListFilter):
    """
    You need to use this filter if your related model (that you want to filter by) is on a different
    app than your original model.
    """

    pass


class LazyAutocompleteListFilter(
    LazyAutocompleteListFilterMixin, AutocompleteListFilter
):
    pass


class LazyRelatedAutocompleteListFilter(
    LazyAutocompleteListFilterMixin, RelatedAutocompleteListFilter
):
    pass


class AutocompleteMultipleListFilter(MultiSelectRelatedFilter, AutocompleteMixin):
    template = "more_admin_filters/autocomplete_multiple_list_filter.html"

    def _get_app_label(self):
        return self.field.model._meta.app_label

    def _get_model_name(self):
        return self.field.model._meta.model_name

    def __init__(self, field, request, params, model, model_admin, *args, **kwargs):
        self.values = []
        super().__init__(field, request, params, model, model_admin, *args, **kwargs)

        self.app_label = model._meta.app_label
        self.model = model
        self.model_name = field.model._meta.model_name
        self.related_model = field.related_model
        self.related_app_label = field.related_model._meta.app_label
        self.related_model_name = field.related_model._meta.model_name
        self.request = request
        self.field_path = kwargs["field_path"]

    def queryset(self, request, queryset):
        raw_value = self.used_parameters.get(f"{self.field_path}__id__in")

        if not raw_value:
            return queryset

        # values are comma-separated IDs
        if isinstance(raw_value, str):
            values = [v for v in raw_value.split(",") if v]
        elif isinstance(raw_value, list):
            values = raw_value
        else:
            values = []

        self.values = values

        try:
            return queryset.filter(**{f"{self.field_path}__id__in": values})
        except ValueError:
            return queryset.none()

    def choices(self, changelist):
        autocomplete_url = reverse("admin:autocomplete")
        selected_items = []

        if self.values:
            try:
                selected_items = list(self.field.related_model.objects.filter(id__in=self.values))
            except ValueError:
                selected_items = []

        return (
            {
                "app_label": self._get_app_label(),
                "model_name": self._get_model_name(),
                "field_name": self.field.name,
                "autocomplete_url": autocomplete_url,
                "selected_items": selected_items,
            },
        )


class RelatedAutocompleteMultipleListFilter(AutocompleteMultipleListFilter):
    """
    Use this filter if your related model (that you want to filter by)
    is in a different app than your original model.
    """

    pass
