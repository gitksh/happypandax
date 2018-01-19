"""
Tags
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

from happypanda.common import exceptions, utils, constants
from happypanda.core import db, message
from happypanda.interface import enums
from happypanda.core.commands import database_cmd, search_cmd


def _contruct_tags_msg(nstags):
    msg = {}
    _msg = {}
    if nstags:
        for nstag in nstags:
            ns = nstag.namespace.name
            if ns not in msg:
                msg[ns] = []
                _msg[ns] = []

            if nstag.tag.name not in _msg[ns]:
                msg[ns].append(message.Tag(nstag.tag, nstag).json_friendly(include_key=False))
                _msg[ns].append(nstag.tag.name)

    return msg


def get_all_tags(limit: int=100, offset: int=None):
    """
    Get all tags from the db

    Args:
        limit: limit the amount of items returned
        offset: offset the results by n items

    Returns:
        .. code-block:: guess

            {
                namespace : [ tag message object, ...],
                ...
            }
    """
    db_obj = database_cmd.GetModelItems().run(db.NamespaceTags, limit=limit, offset=offset)

    msg = _contruct_tags_msg(db_obj)

    return message.Identity('tags', msg)

def search_tags(search_query: str="",
                search_options: dict = {},
                only_namespace: bool=False,
                only_tag: bool=False,
                limit: int=100,
                offset: int=None,
                ):
    """
    Search for tags

    Args:
        search_query: search string
        search_options: options to apply when filtering, see :ref:`Settings` for available search options
        only_namespace: only search for matching namespace <not implemented yet>
        only_tag: only search for matching tag <not implemented yet>
        limit: limit the amount of items returned
        offset: offset the results by n items

    Returns:
        .. code-block:: guess

            {
                namespace : [ tag message object, ...],
                ...
            }
    """
    if search_options:
        search_option_names = [x.name for x in search_cmd._get_search_options()]
        for n in search_options:
            if n not in search_option_names:
                raise exceptions.APIError(utils.this_function(), "Invalid search option name '{}'".format(n))

    db_model = db.NamespaceTags
    model_ids = search_cmd.ModelFilter().run(db_model, search_query, search_options)

    items = database_cmd.GetModelItems().run(db_model, model_ids, limit=limit, offset=offset)

    msg = _contruct_tags_msg(items)

    return message.Identity('tags', msg)

def get_tags_count():
    """
    Get count of namespacetags in the database

    Returns:
        .. code-block:: guess

            {
                'count' : int
            }
    """

    s = constants.db_session()

    return message.Identity('count', {'count': s.query(db.NamespaceTags).count()})

def get_tags(item_type: enums.ItemType = enums.ItemType.Gallery,
             item_id: int = 0,
             raw: bool = False):
    """
    Get tags for item

    Args:
        item_type: possible items are :attr:`.ItemType.Gallery`, :attr:`.ItemType.Page`,
            :attr:`.ItemType.Grouping`, :attr:`.ItemType.Collection`
        item_id: id of item to fetch tags for
        raw: if true, tags from descendant ItemType's will not be included
            (this only makes sense when ItemType is :attr:`.ItemType.Gallery`)

    Returns:
        .. code-block:: guess

            {
                namespace : [ tag message object, ...],
                ...
            }
    """

    item_type = enums.ItemType.get(item_type)

    _, db_item = item_type._msg_and_model(
        (enums.ItemType.Gallery, enums.ItemType.Collection, enums.ItemType.Grouping, enums.ItemType.Page))

    db_obj = database_cmd.GetModelItems().run(db_item, {item_id})
    if db_obj:
        db_obj = db_obj[0]

    nstags = []
    if db_obj:
        g_objs = []
        if issubclass(db_item, db.TaggableMixin):
            nstags = db_obj.tags.all()
            if not raw and isinstance(db_obj, db.Gallery):
                g_objs.append(db_obj)
        else:
            for g in db_obj.galleries.all():
                nstags.extend(g.tags.all())
                if not raw:
                    g_objs.append(g)

        for g_obj in g_objs:
            for p in g_obj.pages.all():  # TODO: we only need tags
                nstags.extend(p.tags.all())

    msg = _contruct_tags_msg(nstags)

    return message.Identity('tags', msg)


def get_common_tags(item_type: enums.ItemType = enums.ItemType.Collection,
                    item_id: int = 0,
                    limit: int = 10):
    """
    Get the most common tags for item

    Args:
        item_type: possible items are :attr:`.ItemType.Artist`, :attr:`.ItemType.Grouping`, :attr:`.ItemType.Collection`
        item_id: id of item to fetch tags for
        limit: limit amount of tags returned

    Returns:
        .. code-block:: guess

            {
                namespace : [ tag message object, ...],
                ...
            }
    """
    item_type = enums.ItemType.get(item_type)

    _, db_item = item_type._msg_and_model(
        (enums.ItemType.Artist, enums.ItemType.Collection, enums.ItemType.Grouping))

    nstags = database_cmd.MostCommonTags().run(db_item, item_id, limit)
    msg = _contruct_tags_msg(nstags)

    return message.Identity('tags', msg)
