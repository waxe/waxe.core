import re
import webob


# Basically the same function as in tw2.core.validation.
# We don't want to have a lot of dependancies just for this function.
def unflatten_params(params):
    """This performs the first stage of validation. It takes a dictionary where
    some keys will be compound names, such as "form:subform:field" and converts
    this into a nested dict/list structure. It also performs unicode decoding.
    """
    if isinstance(params, webob.MultiDict):
        params = params.mixed()
    # TODO: the encoding can be in the given params, use it!
    enc = 'utf-8'
    for p in params:
        if isinstance(params[p], str):
            # Can raise an exception!
            params[p] = params[p].decode(enc)

    out = {}
    for pname in params:
        dct = out
        elements = pname.split(':')
        for e in elements[:-1]:
            dct = dct.setdefault(e, {})
        dct[elements[-1]] = params[pname]

    numdict_to_list(out)
    return out

number_re = re.compile('^\d+$')


def numdict_to_list(dct):
    for k, v in dct.items():
        if isinstance(v, dict):
            numdict_to_list(v)
            if all(number_re.match(k) for k in v):
                dct[k] = [v[x] for x in sorted(v, key=int)]
