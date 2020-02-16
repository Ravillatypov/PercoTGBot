from tortoise import models, fields

from app.settings import ADMIN_USERNAME


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


class User(TimestampModel):
    chat_id = fields.BigIntField(pk=True)
    username = fields.CharField(max_length=100, index=True)
    first_name = fields.CharField(max_length=100)
    last_name = fields.CharField(max_length=100)
    is_active = fields.BooleanField(null=True)
    doors = fields.ManyToManyField('models.Door', related_name='users')

    @property
    def is_admin(self) -> bool:
        return self.username == ADMIN_USERNAME

    @property
    def full_name(self) -> str:
        return f'{self.first_name} {self.last_name}'


class DoorMessage(TimestampModel):
    door = fields.ForeignKeyField('models.Door', related_name='messages')
    user = fields.ForeignKeyField('models.User', related_name='messages')
    message_id = fields.BigIntField()
