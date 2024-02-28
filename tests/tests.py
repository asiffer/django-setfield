import json
import os
from tempfile import NamedTemporaryFile

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db.models import ExpressionWrapper, F, IntegerField
from django.test import TestCase

from .models import TestModel, TestModelWithDefault


class ModelTest(TestCase):

    def test_field_create(self):
        size = 1
        tags = TestModel.OPTIONS[:size]
        m = TestModel.objects.create(tags=tags)
        assert isinstance(
            m.tags, type(tags)
        ), f"bad type (expect '{type(tags)}' got {type(m.tags)})"
        assert len(m.tags) == size, f"bad size (expect {size}, got {len(m.tags)})"

    def test_field_pycreate(self):
        m = TestModel()
        assert isinstance(m.tags, set), f"bad type (expect 'set' got {type(m.tags)})"
        assert len(m.tags) == 0, f"bad size (expect 0, got {len(m.tags)})"

        m.tags.add(TestModel.OPTIONS[0])
        m.save()
        assert len(m.tags) == 1, f"bad size (expect 1, got {len(m.tags)})"

        # previous = set.copy(m.tags)
        try:
            # try to pass value that is not valid
            m.tags.add("???")
            m.save()
        except ValidationError:
            pass

        # the model value remains invalid
        try:
            m.save()
        except ValidationError:
            pass

        m.tags = set()
        m.save()

    def test_bad_field_value(self):
        m = None
        tags = ["???"]
        try:
            m = TestModel.objects.create(tags=tags)
        except ValidationError:
            pass

        assert m is None, m.tags

    def test_half_bad_field_value(self):
        m = None
        tags = ["???", TestModel.OPTIONS[0]]
        try:
            m = TestModel.objects.create(tags=tags)
        except (ValidationError, AssertionError):
            pass

        assert m is None

    def test_update_field(self):
        tags = [TestModel.OPTIONS[0]]
        m = TestModel.objects.create(tags=tags)
        assert isinstance(
            m.tags, type(tags)
        ), f"bad type (expect '{type(tags)}' got {type(m.tags)})"
        # ensure we have a set
        m.refresh_from_db()
        assert isinstance(m.tags, set), f"bad type (expect 'set' got {type(m.tags)})"

        m.tags.add(TestModel.OPTIONS[1])
        s = set(TestModel.OPTIONS[:2])
        assert m.tags == s, f"bad value (expect {s}, got {m.tags})"
        m.save()
        assert m.tags == s, f"bad value (expect {s}, got {m.tags})"

        m.tags = [TestModel.OPTIONS[1]]
        m.save()
        assert len(m.tags) == 1


class ModelWithDefaultTest(TestCase):

    def test_field_create(self):
        m = TestModelWithDefault.objects.create()
        assert isinstance(m.tags, set), f"bad type (expect '{set}' got {type(m.tags)})"
        default = TestModelWithDefault.tags.field.get_default()
        assert m.tags == default, f"bad value (expect {default}, got {m.tags})"


class FixtureTestCase(TestCase):
    def test_loaddata(self):
        "Test my custom command."

        fixture = [
            {
                "model": "tests.testmodel",
                "pk": 1,
                "fields": {"tags": ["NANA"]},
            }
        ]
        directory = "/tmp"
        file = NamedTemporaryFile(suffix=".json", dir=directory, delete=False)

        file.write(json.dumps(fixture).encode())
        file.close()
        # with open(file.name, "w") as fp:
        #     json.dump(fixture, fp)
        p = os.path.join(directory, file.name)
        args = [p]
        opts = {}
        call_command("loaddata", *args, **opts)

        os.remove(p)
        obj = TestModel.objects.get(pk=fixture[0]["pk"])
        self.assertEqual(obj.tags, set(fixture[0]["fields"]["tags"]))

    def test_dumpdata(self):
        "Test my custom command."

        print("=" * 80)
        tags = {"NANA", "TOMTOM"}
        TestModel.objects.create(tags=tags)
        fixture = [
            {
                "model": "tests.testmodel",
                "pk": 1,
                "fields": {"tags": list(tags)},
            }
        ]
        directory = "/tmp"
        p = os.path.join(directory, "django_setfield_dump.json")
        opts = {"indent": 4, "output": p}
        args = ["tests.TestModel"]
        call_command("dumpdata", *args, **opts)

        with open(p, "r", encoding="utf-8") as fp:
            fix = json.load(fp)

        self.assertDictEqual(fixture[0], fix[0])
        os.remove(p)


class QueryTestCase(TestCase):
    def setUp(self) -> None:
        TestModel.objects.all().delete()
        return super().setUp()

    def test_query(self):
        index = 1
        tags = {TestModel.OPTIONS[index - 1]}
        TestModel.objects.create(tags=tags)

        result = TestModel.objects.annotate(
            tag_filter=ExpressionWrapper(
                F("tags").bitand(index), output_field=IntegerField()
            )
        ).filter(tag_filter__gt=0)
        assert len(result) == 1

    def test_custom_lookup(self):
        tags = set(TestModel.OPTIONS)
        TestModel.objects.create(tags=tags)
        for t in tags:
            assert (
                TestModel.objects.filter(tags__includes=t).count() == 1
            ), TestModel.objects.filter(tags__includes=t).all()
