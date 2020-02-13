from tortoise import models, fields
from app.settings import ADMIN_PHONES


class TimestampModel(models.Model):
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    def __str__(self):
        model = self.__class__.__name__
        detail = ', '.join(
            (f'{k}: "{self.__getattribute__(k)}"' for k, v in self._meta.fields_map.items() if v.field_type and v)
        )
        return f'<{model}>: {detail}'

    class Meta:
        abstract = True


class Door(TimestampModel):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)


class Group(TimestampModel):
    doors = fields.ManyToManyField('models.Door', related_name='groups')
    name = fields.CharField(max_length=100, unique=True)


class User(TimestampModel):
    chat_id = fields.BigIntField(null=True)
    phone = fields.CharField(max_length=12)
    code = fields.CharField(max_length=10)
    name = fields.CharField(max_length=100)
    group = fields.ForeignKeyField('models.Group', related_name='users')

    @property
    def is_admin(self) -> bool:
        return self.phone in ADMIN_PHONES

    @property
    def doors(self):
        if self.is_admin:
            return Door.all()
        return self.group.doors.all()
