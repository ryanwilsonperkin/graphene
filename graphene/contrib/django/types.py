import six

from ...core.types import BaseObjectType, ObjectTypeMeta
from ...relay.fields import GlobalIDField
from ...relay.types import BaseNode
from .converter import convert_django_field
from .options import DjangoOptions
from .utils import get_reverse_fields


class DjangoObjectTypeMeta(ObjectTypeMeta):
    options_cls = DjangoOptions

    def is_interface(cls, parents):
        return DjangoInterface in parents

    def add_extra_fields(cls):
        if not cls._meta.model:
            return
        only_fields = cls._meta.only_fields
        reverse_fields = get_reverse_fields(cls._meta.model)
        all_fields = sorted(list(cls._meta.model._meta.fields) +
                            list(cls._meta.model._meta.local_many_to_many))
        all_fields += list(reverse_fields)
        already_created_fields = {f.attname for f in cls._meta.local_fields}

        for field in all_fields:
            is_not_in_only = only_fields and field.name not in only_fields
            is_already_created = field.name in already_created_fields
            is_excluded = field.name in cls._meta.exclude_fields or is_already_created
            if is_not_in_only or is_excluded:
                # We skip this field if we specify only_fields and is not
                # in there. Or when we excldue this field in exclude_fields
                continue
            converted_field = convert_django_field(field)
            cls.add_to_class(field.name, converted_field)


class InstanceObjectType(BaseObjectType):

    def __init__(self, instance=None):
        self.instance = instance
        super(InstanceObjectType, self).__init__()

    def __getattr__(self, attr):
        return getattr(self.instance, attr)


class DjangoObjectType(six.with_metaclass(
        DjangoObjectTypeMeta, InstanceObjectType)):
    pass


class DjangoInterface(six.with_metaclass(
        DjangoObjectTypeMeta, InstanceObjectType)):
    pass


class DjangoNode(BaseNode, DjangoInterface):
    id = GlobalIDField()

    @classmethod
    def get_node(cls, id):
        instance = cls._meta.model.objects.filter(id=id).first()
        return cls(instance)
