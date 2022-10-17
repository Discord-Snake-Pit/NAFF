import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import emoji

from naff.client.mixins.serialization import DictSerializationMixin
from naff.client.utils.attr_converters import list_converter
from naff.client.utils.attr_converters import optional
from naff.client.utils.attr_utils import define, field
from naff.client.utils.serializer import dict_filter_none, no_export_meta
from naff.models.discord.base import ClientObject
from naff.models.discord.snowflake import SnowflakeObject, to_snowflake

if TYPE_CHECKING:
    from naff.client import Client
    from naff.models.discord.guild import Guild
    from naff.models.discord.user import User, Member
    from naff.models.discord.role import Role
    from naff.models.discord.snowflake import Snowflake_Type

__all__ = ("PartialEmoji", "CustomEmoji", "process_emoji_req_format", "process_emoji")

emoji_regex = re.compile(r"<?(a)?:(\w*):(\d*)>?")


@define(kw_only=False)
class PartialEmoji(SnowflakeObject, DictSerializationMixin):
    """Represent a basic ("partial") emoji used in discord."""

    id: Optional["Snowflake_Type"] = field(
        repr=True, default=None, converter=optional(to_snowflake)
    )  # can be None for Standard Emoji
    """The custom emoji id. Leave empty if you are using standard unicode emoji."""
    name: Optional[str] = field(repr=True, default=None)
    """The custom emoji name, or standard unicode emoji in string"""
    animated: bool = field(repr=True, default=False)
    """Whether this emoji is animated"""

    @classmethod
    def from_str(cls, emoji_str: str, *, language: str = "alias") -> Optional["PartialEmoji"]:
        """
        Generate a PartialEmoji from a discord Emoji string representation, or unicode emoji.

        Handles:
            <:emoji_name:emoji_id>
            :emoji_name:emoji_id
            <a:emoji_name:emoji_id>
            a:emoji_name:emoji_id
            👋
            :wave:

        Args:
            emoji_str: The string representation an emoji
            language: The language to use for the unicode emoji parsing

        Returns:
            A PartialEmoji object

        Raises:
            ValueError: if the string cannot be parsed

        """
        parsed = emoji_regex.findall(emoji_str)
        if parsed:
            parsed = tuple(filter(None, parsed[0]))
            if len(parsed) == 3:
                return cls(name=parsed[1], id=parsed[2], animated=True)
            elif len(parsed) == 2:
                return cls(name=parsed[0], id=parsed[1])
            else:
                _name = emoji.emojize(emoji_str, language=language)
                _emoji_list = emoji.distinct_emoji_list(_name)
                if _emoji_list:
                    return cls(name=_emoji_list[0])
        else:
            # check if it's a unicode emoji
            _emoji_list = emoji.distinct_emoji_list(emoji_str)
            if _emoji_list:
                return cls(name=_emoji_list[0])
        return None

    def __str__(self) -> str:
        s = self.req_format
        if self.id:
            s = f"<{'a:' if self.animated else ':'}{s}>"
        return s

    def __eq__(self, other) -> bool:
        if not isinstance(other, PartialEmoji):
            return False
        if self.id:
            return self.id == other.id
        return self.name == other.name

    @property
    def req_format(self) -> str:
        """Format used for web request."""
        if self.id:
            return f"{self.name}:{self.id}"
        else:
            return self.name


@define()
class CustomEmoji(PartialEmoji, ClientObject):
    """Represent a custom emoji in a guild with all its properties."""

    _client: "Client" = field(metadata=no_export_meta)

    require_colons: bool = field(default=False)
    """Whether this emoji must be wrapped in colons"""
    managed: bool = field(default=False)
    """Whether this emoji is managed"""
    available: bool = field(default=False)
    """Whether this emoji can be used, may be false due to loss of Server Boosts."""

    _creator_id: Optional["Snowflake_Type"] = field(default=None, converter=optional(to_snowflake))
    _role_ids: List["Snowflake_Type"] = field(factory=list, converter=optional(list_converter(to_snowflake)))
    _guild_id: "Snowflake_Type" = field(default=None, converter=to_snowflake)

    @classmethod
    def _process_dict(cls, data: Dict[str, Any], client: "Client") -> Dict[str, Any]:
        creator_dict = data.pop("user", None)
        data["creator_id"] = client.cache.place_user_data(creator_dict).id if creator_dict else None

        if "roles" in data:
            data["role_ids"] = data.pop("roles")

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], client: "Client", guild_id: int) -> "CustomEmoji":
        data = cls._process_dict(data, client)
        return cls(client=client, guild_id=guild_id, **cls._filter_kwargs(data, cls._get_init_keys()))

    @property
    def guild(self) -> "Guild":
        """The guild this emoji belongs to."""
        return self._client.cache.get_guild(self._guild_id)

    @property
    def creator(self) -> Optional[Union["Member", "User"]]:
        """The member that created this emoji."""
        return self._client.cache.get_member(self._creator_id, self._guild_id) or self._client.cache.get_user(
            self._creator_id
        )

    @property
    def roles(self) -> List["Role"]:
        """The roles allowed to use this emoji."""
        return [self._client.cache.get_role(role_id) for role_id in self._role_ids]

    @property
    def is_usable(self) -> bool:
        """Determines if this emoji is usable by the current user."""
        if not self.available:
            return False

        guild = self.guild
        return any(e_role_id in guild.me._role_ids for e_role_id in self._role_ids)

    async def edit(
        self,
        name: Optional[str] = None,
        roles: Optional[List[Union["Snowflake_Type", "Role"]]] = None,
        reason: Optional[str] = None,
    ) -> "CustomEmoji":
        """
        Modify the custom emoji information.

        Args:
            name: The name of the emoji.
            roles: The roles allowed to use this emoji.
            reason: Attach a reason to this action, used for audit logs.

        Returns:
            The newly modified custom emoji.

        """
        data_payload = dict_filter_none(
            {
                "name": name,
                "roles": roles,
            }
        )

        updated_data = await self._client.http.modify_guild_emoji(data_payload, self._guild_id, self.id, reason=reason)
        self.update_from_dict(updated_data)
        return self

    async def delete(self, reason: Optional[str] = None) -> None:
        """
        Deletes the custom emoji from the guild.

        Args:
            reason: Attach a reason to this action, used for audit logs.

        """
        if not self._guild_id:
            raise ValueError("Cannot delete emoji, no guild id set.")

        await self._client.http.delete_guild_emoji(self._guild_id, self.id, reason=reason)


def process_emoji_req_format(emoji: Optional[Union[PartialEmoji, dict, str]]) -> Optional[str]:
    """
    Processes the emoji parameter into the str format required by the API.

    Args:
        emoji: The emoji to process.

    Returns:
        formatted string for discord

    """
    if not emoji:
        return emoji

    if isinstance(emoji, str):
        emoji = PartialEmoji.from_str(emoji)

    if isinstance(emoji, dict):
        emoji = PartialEmoji.from_dict(emoji)

    if isinstance(emoji, PartialEmoji):
        return emoji.req_format

    raise ValueError(f"Invalid emoji: {emoji}")


def process_emoji(emoji: Optional[Union[PartialEmoji, dict, str]]) -> Optional[dict]:
    """
    Processes the emoji parameter into the dictionary format required by the API.

    Args:
        emoji: The emoji to process.

    Returns:
        formatted dictionary for discord

    """
    if not emoji:
        return emoji

    if isinstance(emoji, dict):
        return emoji

    if isinstance(emoji, str):
        emoji = PartialEmoji.from_str(emoji)

    if isinstance(emoji, PartialEmoji):
        return emoji.to_dict()

    raise ValueError(f"Invalid emoji: {emoji}")
