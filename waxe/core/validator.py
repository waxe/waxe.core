import tw2.core as twc
import bcrypt


class BCryptValidator(twc.Validator):

    def _convert_to_python(self, value, state):
        if not value:
            return value
        return bcrypt.hashpw(value, bcrypt.gensalt())
