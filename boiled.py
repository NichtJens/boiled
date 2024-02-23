import contextlib
import functools
import inspect


METHODS_IGNORE = [
    "api_client"
]

METHODS_IGNORE_SUFFICES = [
    "with_http_info",
    "without_preload_content"
]

METHODS_ALLOWED_SUFFICES = [
    "get",
    "post",
    "put"
]



def boiled(openapi_client):
    """
    Wraps openapi_client to remove boilerplate
    """
    @contextlib.contextmanager
    def client(*args, **kwargs):
        configuration = openapi_client.Configuration(*args, **kwargs)
        with openapi_client.ApiClient(configuration) as api_client:
            api_instance = openapi_client.DefaultApi(api_client)
            yield wrap_api(api_instance)
    return client


def wrap_api(api):
    """
    Wraps api by wrapping each of its method
    """
    for n in get_methods(api):
        f = getattr(api, n)
        w = wrap_method(f)
        setattr(api, n, w)

    return api


def get_methods(api):
    """
    Iterate over user methods of api
    Skips over dunder methods and methods with names ending on entries from METHODS_IGNORE_SUFFICES
    Raises ValueError for methods with suffix not in METHODS_ALLOWED_SUFFICES
    """
    for n in dir(api):
        if n.startswith("_"):
            continue

        if n in METHODS_IGNORE:
            continue

        try:
            for ignore_suffix in METHODS_IGNORE_SUFFICES:
                if n.endswith(f"_{ignore_suffix}"):
                    raise Exception
        except Exception:
            continue

        suffix = n.rsplit("_", 1)[-1]
        if suffix not in METHODS_ALLOWED_SUFFICES:
            raise ValueError(f'suffix "{suffix}" for method "{n}" not from allowed: {ALLOWED_SUFFICES}')

        yield n


def wrap_method(func):
    """
    Wraps func such that the call signature matches the signature of the single argument with an adjusted docstring
    """
    collected = get_argument(func)
    if not collected:
        return func

    arg_name, ConfigType = collected.popitem()

    extra_doc = signature_to_doc(ConfigType)

    ConfigType = wrap_config_type(ConfigType)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        cfg = ConfigType(*args, **kwargs)
        wrapped_args = {arg_name: cfg}
        return func(**wrapped_args)

    wrapper.__doc__ += extra_doc
    wrapper.__signature__ = ConfigType.__signature__

    return wrapper


def get_argument(func):
    """
    Retrieves user argument (i.e., name not starting with "_") from func's annotations, raises ValueError if ambiguous
    """
    collected = {}
    anno = func.__annotations__
    for k, v in anno.items():
        if k.startswith("_"):
            continue
        if k == "return":
            continue
        #TODO: check if v is typing.Union?
        collected[k] = v.__args__[0]

#    if collected:
#        print(f.__name__, collected, sep="\t")

    n_collected = len(collected)

    if n_collected == 0:
        return None

    if n_collected != 1:
        raise ValueError(f'found ambiguous arguments for method "{f.__name__}": {collected}')

    return collected


def signature_to_doc(ConfigType):
    """
    Converts the signature of ConfigType to a docstring
    """
    fn = ConfigType.__name__
    header = f"Parameters for {fn}:"
    line   = "-" * len(header)

    res = ["", header, line]

    params = ConfigType.__signature__.parameters
    res.extend(
        str(v) for k, v in params.items()
    )

    res.append("")

    res = indent(res)
    return "\n".join(res)


def indent(seq, n=8):
    """
    Indent a sequence of values to depth n
    """
    spaces = " " * n
    return [f"{spaces}{i}" if i else i for i in seq]


def wrap_config_type(ConfigType):
    """
    Wraps ConfigType (cf. make_config_type_wrapper)
    """
    args, kwargs = get_args_kwargs(ConfigType)
    return make_config_type_wrapper(ConfigType, args, kwargs)


def get_args_kwargs(ConfigType):
    """
    Read parameters from signature and split positional and keyword args
    """
    args = []
    kwargs = {}

    params = ConfigType.__signature__.parameters
    for k, v in params.items():
        if k.startswith("_"):
            continue

        if v.default == v.empty:
            args.append(k)
        else:
            kwargs[k] = v.default

    return args, kwargs


def make_config_type_wrapper(func_inner, pos, kw):
    """
    ConfigType expects mandatory params also as keyword args
    Assemble a dict of mandatory params from
        pos (names of positional args) and
        given values from *args when the returned function is called
    Adjust the signature
    """
    @functools.wraps(func_inner)
    def func_outer(*args, **kwargs):
        dargs = dict(zip(pos, args))
        return func_inner(**dargs, **kwargs)
    func_outer.__signature__ = make_signature(pos, kw)
    return func_outer


def make_signature(pos, kw):
    """
    Generate a function signature from
        pos: names of the positional parameters
        kw:  mapping of name to default value for keyword parameters
    """
    params = make_params_pos(pos) + make_params_kw(kw)
    return inspect.Signature(parameters=params)


def make_params_pos(pos, kind=inspect.Parameter.POSITIONAL_OR_KEYWORD):
    """
    Generate list of positional parameters
    """
    return [inspect.Parameter(n, kind) for n in pos]


def make_params_kw(kw, kind=inspect.Parameter.POSITIONAL_OR_KEYWORD):
    """
    Generate list of keyword parameters
    """
    return [inspect.Parameter(n, kind, default=v) for n, v in kw.items()]



