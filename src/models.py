from tortoise import fields
from tortoise.models import Model
import enum

class PollStatus(str, enum.Enum):
    """Poll lifecycle states"""
    ACTIVE = "active"
    ENDED = "ended"
    CANCELLED = "cancelled"

class Poll(Model):
    """Main poll model - stores poll configuration and metadata"""
    
    id = fields.IntField(pk=True)
    
    # Discord identifiers
    guild_id = fields.BigIntField(index=True)
    channel_id = fields.BigIntField()
    message_id = fields.BigIntField(unique=True, null=True)
    creator_id = fields.BigIntField()
    
    # Poll configuration
    question = fields.TextField()
    is_anonymous = fields.BooleanField(default=False)
    allow_multiple_votes = fields.BooleanField(default=False)
    
    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True)
    end_date = fields.DatetimeField(null=True)
    
    # Status
    status = fields.CharEnumField(PollStatus, default=PollStatus.ACTIVE)
    
    # Relations
    options: fields.ReverseRelation["PollOption"]
    votes: fields.ReverseRelation["Vote"]
    subscribers: fields.ReverseRelation["PollSubscriber"]
    edit_logs: fields.ReverseRelation["PollEditLog"]
    
    class Meta:
        table = "polls"
        indexes = [
            ("guild_id", "status"),
            ("end_date",),
        ]

class PollOption(Model):
    """Individual poll options/choices"""
    
    id = fields.IntField(pk=True)
    poll = fields.ForeignKeyField(
        "models.Poll",
        related_name="options",
        on_delete=fields.CASCADE
    )
    
    # Option data
    text = fields.CharField(max_length=100)
    position = fields.IntField()  # 0-9
    
    # Metadata
    created_at = fields.DatetimeField(auto_now_add=True)
    created_by = fields.BigIntField()
    
    # Relations
    votes: fields.ReverseRelation["Vote"]
    
    class Meta:
        table = "poll_options"
        unique_together = (("poll_id", "position"),)
        ordering = ["position"]

class Vote(Model):
    """Individual votes cast on poll options"""
    
    id = fields.IntField(pk=True)
    poll = fields.ForeignKeyField(
        "models.Poll",
        related_name="votes",
        on_delete=fields.CASCADE
    )
    option = fields.ForeignKeyField(
        "models.PollOption",
        related_name="votes",
        on_delete=fields.CASCADE
    )
    
    # Voter info
    user_id = fields.BigIntField(index=True)
    
    # Metadata
    voted_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "votes"
        indexes = [
            ("poll_id", "user_id"),
            ("option_id",),
        ]

class PollSubscriber(Model):
    """Users subscribed to poll result notifications"""
    
    id = fields.IntField(pk=True)
    poll = fields.ForeignKeyField(
        "models.Poll",
        related_name="subscribers",
        on_delete=fields.CASCADE
    )
    user_id = fields.BigIntField()
    
    # Metadata
    subscribed_at = fields.DatetimeField(auto_now_add=True)
    notified = fields.BooleanField(default=False)
    
    class Meta:
        table = "poll_subscribers"
        unique_together = (("poll_id", "user_id"),)

class PollEditLog(Model):
    """Track poll modifications for audit trail"""
    
    id = fields.IntField(pk=True)
    poll = fields.ForeignKeyField(
        "models.Poll",
        related_name="edit_logs",
        on_delete=fields.CASCADE
    )
    
    # What changed
    action = fields.CharField(max_length=50)  # "option_added", "option_removed", "poll_ended", etc.
    details = fields.JSONField(null=True)
    
    # Who did it
    user_id = fields.BigIntField()
    
    # When
    timestamp = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "poll_edit_logs"
        indexes = [("poll_id", "timestamp")]