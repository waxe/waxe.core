import tw2.core.testbase as tb
from tw2.core.validation import ValidationError
from ..validator import BCryptValidator
import bcrypt
from nose.tools import eq_


class TestBCryptValidator(tb.ValidatorTest):
    validator = BCryptValidator
    attrs = [{}, {'required': True}]
    params = ['', '']
    expected = [None, ValidationError]

    from_python_attrs = [{}, {'required': True}]
    from_python_params = ['', 'asdf']
    from_python_expected = ['', 'asdf']

    def test__convert_to_python(self):
        state = None
        v = BCryptValidator()
        res = v._convert_to_python('', state)
        eq_(res, '')

        res = v._convert_to_python('toto', state)
        eq_(bcrypt.hashpw('toto', res), res)
