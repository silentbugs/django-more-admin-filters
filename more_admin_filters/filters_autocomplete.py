from .filters import RelatedDropdownFilter

from django.contrib.admin.widgets import AutocompleteMixin
from django.urls import reverse


class AutocompleteListFilter(RelatedDropdownFilter, AutocompleteMixin):
    template = "more_admin_filters/autocomplete_list_filter.html"

    def _get_app_label(self):
        return self.app_label

    def _get_model_name(self):
        return self.model_name

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


class RelatedAutocompleteListFilter(AutocompleteListFilter):
    """
    You need to use this filter if your related model (that you want to filter by) is on a different
    app than your original model.
    """

    def _get_app_label(self):
        return self.field.remote_field.related_model._meta.app_label

    def _get_model_name(self):
        return self.field.remote_field.related_model._meta.model_name
