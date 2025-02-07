from django.conf import settings


class AutocompleteListFilterMixin:
    class Media:
        css = {
            "screen": [
                (
                    "admin/css/vendor/select2/select2.css"
                    if settings.DEBUG
                    else "admin/css/vendor/select2/select2.min.css"
                ),
                "admin/css/autocomplete.css",
            ],
        }
        js = [
            (
                "admin/js/vendor/select2/select2.full.js"
                if settings.DEBUG
                else "admin/js/vendor/select2/select2.full.min.js"
            ),
            "admin/js/jquery.init.js",
            "admin/js/autocomplete.js",
        ]
