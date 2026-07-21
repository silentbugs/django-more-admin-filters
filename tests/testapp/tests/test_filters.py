

from unittest import mock

from django.contrib.admin import AdminSite, ModelAdmin
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase
from django.urls import reverse

from more_admin_filters.filters import (
    RelatedDropdownFilter,
)
from more_admin_filters.filters_autocomplete import AutocompleteOnlyListFilter
from more_admin_filters import (
    AutocompleteListFilter,
    LazyAutocompleteListFilter,
    LazyRelatedAutocompleteListFilter,
    RelatedAutocompleteListFilter,
)

from ..management.commands.createtestdata import create_test_data
from ..models import ModelA

# Print python and django version for easier debugging.
import sys, django
print("Python version:", sys.version)
print("Django version:", django.get_version())


class FilterTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_test_data()

    def setUp(self):
        self.admin = User.objects.get(username='admin')
        self.client.force_login(self.admin)
        self.url = reverse('admin:testapp_modela_changelist')

    def test_01_dropdown(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

        # the dropdown widget should have been loaded for dropdown_gt3
        self.assertIn('dropdown-gt3_filter_select', resp.content.decode('utf8'))
        # but not for dropdown_lte3
        self.assertNotIn('dropdown-lte3_filter_select', resp.content.decode('utf8'))

        # check other dropdown widgets
        self.assertIn('multiselect-dropdown_select', resp.content.decode('utf8'))
        self.assertIn('choices-dropdown_filter_select', resp.content.decode('utf8'))
        self.assertIn('related-dropdown_filter_select', resp.content.decode('utf8'))
        self.assertIn('multiselect-related-dropdown_select', resp.content.decode('utf8'))

    def test_02_filtering(self):
        queries = (
            ('', 36),
            ('dropdown_gt3=1&dropdown_lte3__isnull=True', 3),
            ('dropdown_gt3=1&multiselect_dropdown__in=3', 3),
            ('dropdown_gt3=1&multiselect_dropdown__in=3,4,5', 6),
            ('choices_dropdown__exact=3&multiselect_dropdown__in=0,1,2', 2),
            ('multiselect_dropdown__in=0,1,2&related_dropdown__id__exact=6', 1),
            ('related_dropdown__id__exact=6&multiselect_dropdown__in=3,4,5', 0),
            ('multiselect_dropdown__in=3,4,5&multiselect_related__id__in=35,34,33,32', 3),
            ('multiselect_dropdown__in=3,4,5&multiselect_related_dropdown__id__in=29,30,31,32,33,34,35', 4),
            ('boolean_annotation__exact=1&multiselect__in=0,2,4', 14),
        )
        for query, count in queries:
            resp = self.client.get(self.url + '?' + query)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('{} selected'.format(count), resp.content.decode('utf8'))

    def test_03_multiselect_isnull_issue(self):
        queries = [
            'multiselect__isnull=Truee',
            'multiselect_dropdown__isnull=True',
            'multiselect_related__isnull=Truee',
        ]
        for query in queries:
            resp = self.client.get(self.url + '?' + query)
            self.assertEqual(resp.status_code, 200)


class AutocompleteFilterTest(TestCase):
    def test_autocomplete_templates_rely_on_django_initialization(self):
        choices = ({
            "app_label": "testapp",
            "model_name": "modela",
            "field_name": "related_dropdown",
            "autocomplete_url": reverse("admin:autocomplete"),
        },)
        context = {
            "choices": choices,
            "spec": mock.Mock(field_path="related_dropdown"),
            "title": "Related dropdown",
        }

        for template_name in (
            "more_admin_filters/autocomplete_list_filter.html",
            "more_admin_filters/autocomplete_multiple_list_filter.html",
        ):
            with self.subTest(template_name=template_name):
                rendered = render_to_string(template_name, context)
                self.assertNotIn(".djangoAdminSelect2(", rendered)
                self.assertIn('class="admin-autocomplete"', rendered)

    def test_autocomplete_filters_use_autocomplete_template(self):
        filter_classes = (
            AutocompleteListFilter,
            AutocompleteOnlyListFilter,
            RelatedAutocompleteListFilter,
            LazyAutocompleteListFilter,
            LazyRelatedAutocompleteListFilter,
        )

        for filter_class in filter_classes:
            with self.subTest(filter_class=filter_class.__name__):
                self.assertEqual(
                    filter_class.template,
                    "more_admin_filters/autocomplete_list_filter.html",
                )

    def test_autocomplete_choices_include_source_field_metadata(self):
        filter_classes = (
            AutocompleteListFilter,
            AutocompleteOnlyListFilter,
            RelatedAutocompleteListFilter,
            LazyAutocompleteListFilter,
            LazyRelatedAutocompleteListFilter,
        )

        for filter_class in filter_classes:
            with self.subTest(filter_class=filter_class.__name__):
                autocomplete_filter = self.make_filter(filter_class)
                choice = autocomplete_filter.choices(None)[0]

                self.assertEqual(choice["app_label"], "testapp")
                self.assertEqual(choice["model_name"], "modela")
                self.assertEqual(choice["field_name"], "related_dropdown")

    def test_autocomplete_choices_without_selection_do_not_query(self):
        autocomplete_filter = self.make_filter(AutocompleteListFilter)

        with self.assertNumQueries(0):
            choice = autocomplete_filter.choices(None)[0]

        self.assertEqual(choice["selected_item"], "")

    def setUp(self):
        self.field = ModelA._meta.get_field("related_dropdown")
        self.request = RequestFactory().get("/")
        self.model_admin = ModelAdmin(ModelA, AdminSite())

    def make_filter(self, filter_class):
        return filter_class(
            self.field,
            self.request,
            {},
            ModelA,
            self.model_admin,
            field_path="related_dropdown",
        )

    def test_autocomplete_filters_do_not_build_related_field_choices(self):
        filter_classes = (
            LazyAutocompleteListFilter,
            LazyRelatedAutocompleteListFilter,
        )

        for filter_class in filter_classes:
            with self.subTest(filter_class=filter_class.__name__):
                with mock.patch.object(
                    RelatedDropdownFilter,
                    "field_choices",
                    side_effect=AssertionError("related choices were loaded eagerly"),
                ):
                    with self.assertNumQueries(0):
                        autocomplete_filter = self.make_filter(filter_class)
                        has_output = autocomplete_filter.has_output()

                self.assertEqual(autocomplete_filter.lookup_choices, ())
                self.assertTrue(has_output)

    def test_standard_autocomplete_filters_keep_related_field_choices(self):
        filter_classes = (
            AutocompleteListFilter,
            RelatedAutocompleteListFilter,
        )
        lookup_choices = ((1, "ModelB 1"),)

        for filter_class in filter_classes:
            with self.subTest(filter_class=filter_class.__name__):
                with mock.patch.object(
                    RelatedDropdownFilter,
                    "field_choices",
                    return_value=lookup_choices,
                ) as field_choices:
                    autocomplete_filter = self.make_filter(filter_class)

                field_choices.assert_called_once()
                self.assertEqual(autocomplete_filter.lookup_choices, lookup_choices)
