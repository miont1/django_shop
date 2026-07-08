import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

