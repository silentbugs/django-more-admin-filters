from .filters import ChoicesDropdownFilter, RelatedDropdownFilter


class Select2ChoicesDropdownFilter(ChoicesDropdownFilter):
    template = "more_admin_filters//select2_related_dropdown_filter.html"


class Select2RelatedDropdownFilter(RelatedDropdownFilter):
    template = "more_admin_filters/select2_related_dropdown_filter.html"
