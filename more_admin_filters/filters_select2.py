from .filters import (
    ChoicesDropdownFilter,
    RelatedDropdownFilter,
    DropdownFilter,
    RelatedOnlyDropdownFilter,
)


class Select2Filter:
    template = "more_admin_filters//select2_related_dropdown_filter.html"


class Select2DropdownFilter(Select2Filter, DropdownFilter):
    ...


class Select2ChoicesDropdownFilter(Select2Filter, ChoicesDropdownFilter):
    ...


class Select2RelatedDropdownFilter(Select2Filter, RelatedDropdownFilter):
    ...


class Select2RelatedOnlyDropdownFilter(Select2Filter, RelatedOnlyDropdownFilter):
    ...
