#!/usr/bin/env python
import argparse
import os

import django
from django.conf import settings
from django.core.management import call_command

if __name__ == "__main__":
    os.environ["DJANGO_SETTINGS_MODULE"] = "tests.test_settings"
    os.environ["DJANGO_SUPERUSER_PASSWORD"] = "admin"

    parser = argparse.ArgumentParser(__file__, description="Run a test server")
    parser.add_argument("-r", "--reset", help="Clear the database", action="store_true")
    args = parser.parse_args()

    if args.reset:
        try:
            os.remove(settings.DATABASES["default"]["NAME"])
        except FileNotFoundError:
            pass

    django.setup()

    call_command("makemigrations", "tests")
    call_command("migrate")

    if args.reset:
        call_command(
            "createsuperuser",
            email="admin@localhost",
            username="admin",
            no_input=True,
            interactive=False,
        )

    call_command("runserver")
