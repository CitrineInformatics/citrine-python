import abc


class DocstringMeta(abc.ABCMeta):
    """Metaclass that allows docstring 'inheritance'"""

    def __new__(mcs, classname, bases, cls_dict):
        cls = abc.ABCMeta.__new__(mcs, classname, bases, cls_dict)
        mro = cls.__mro__[1:]
        for name, member in cls_dict.items():
            if not getattr(member, '__doc__'):
                for base in mro:
                    try:
                        member.__doc__ = getattr(base, name).__doc__
                        break
                    except AttributeError:
                        pass
        return cls
