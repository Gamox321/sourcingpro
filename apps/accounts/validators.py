import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class UppercaseValidator:
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _('La contraseña debe contener al menos una mayúscula.'),
                code='password_no_upper',
            )

    def get_help_text(self):
        return _('Tu contraseña debe contener al menos una mayúscula.')


class LowercaseValidator:
    def validate(self, password, user=None):
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _('La contraseña debe contener al menos una minúscula.'),
                code='password_no_lower',
            )

    def get_help_text(self):
        return _('Tu contraseña debe contener al menos una minúscula.')


class NumberValidator:
    def validate(self, password, user=None):
        if not re.search(r'[0-9]', password):
            raise ValidationError(
                _('La contraseña debe contener al menos un número.'),
                code='password_no_number',
            )

    def get_help_text(self):
        return _('Tu contraseña debe contener al menos un número.')


class SpecialCharValidator:
    def validate(self, password, user=None):
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-]', password):
            raise ValidationError(
                _('La contraseña debe contener al menos un carácter especial.'),
                code='password_no_special',
            )

    def get_help_text(self):
        return _('Tu contraseña debe contener al menos un carácter especial (!@#$%^&* etc.).')
