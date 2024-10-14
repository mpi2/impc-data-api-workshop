"""Module for warnings and excepton utils"""

import warnings


# Custom warnings
class InvalidCoreWarning(Warning):
    """Exception raised when the core is not in the expected core names"""


class InvalidFieldWarning(Warning):
    """Exception raised when the field name is not in the expected fields"""


# Custom warning function
def warning_config():
    """Customises formatting and filters for warnings"""

    def custom_warning(message, category, filename, lineno, line=None):
        return f'{category.__name__}: {message}\n'

    warnings.formatwarning = custom_warning
    warnings.simplefilter("always", Warning)
