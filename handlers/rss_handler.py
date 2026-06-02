# handlers/rss_handler.py
from services.rss_filter_service import rss_keyword_store
from utils.api_utils import send_group_message


def handle_rss_keyword_command(event):
    """Handle RSS important keyword management commands."""
    group_id = event["group_id"]
    message = event["message"].strip()

    command_part = message[len("#rsskw"):].strip()
    if not command_part or command_part == "list":
        _send_keyword_list(group_id)
        return

    parts = command_part.split()
    action = parts[0].lower()
    keywords = parts[1:]

    if action == "add":
        if not keywords:
            send_group_message(group_id, "格式错误，请使用: #rsskw add <关键词1> [关键词2] ...")
            return
        added = rss_keyword_store.add_keywords(keywords)
        if added:
            send_group_message(group_id, "已添加RSS重点关键词: " + ", ".join(added))
        else:
            send_group_message(group_id, "没有新增关键词，可能都已存在。")
        return

    if action in {"del", "delete", "remove"}:
        if not keywords:
            send_group_message(group_id, "格式错误，请使用: #rsskw del <关键词1> [关键词2] ...")
            return
        deleted = rss_keyword_store.delete_keywords(keywords)
        if deleted:
            send_group_message(group_id, "已删除RSS重点关键词: " + ", ".join(deleted))
        else:
            send_group_message(group_id, "未找到要删除的关键词。")
        return

    if action == "set":
        if not keywords:
            send_group_message(group_id, "格式错误，请使用: #rsskw set <关键词1> [关键词2] ...")
            return
        updated = rss_keyword_store.set_keywords(keywords)
        send_group_message(group_id, "已设置RSS重点关键词: " + ", ".join(updated))
        return

    if action in {"edit", "update"}:
        if len(keywords) != 2:
            send_group_message(group_id, "格式错误，请使用: #rsskw edit <旧关键词> <新关键词>")
            return
        replaced = rss_keyword_store.replace_keyword(keywords[0], keywords[1])
        if replaced:
            send_group_message(group_id, f"已修改RSS重点关键词: {keywords[0]} -> {keywords[1]}")
        else:
            send_group_message(group_id, f"未找到要修改的关键词: {keywords[0]}")
        return

    if action == "clear":
        rss_keyword_store.clear_keywords()
        send_group_message(group_id, "已清空RSS重点关键词。")
        return

    if action == "help":
        send_group_message(group_id, _keyword_help_text())
        return

    send_group_message(group_id, "未知RSS关键词命令，使用 #rsskw help 查看帮助。")


def _send_keyword_list(group_id):
    keywords = rss_keyword_store.list_keywords()
    if not keywords:
        send_group_message(group_id, "RSS重点关键词为空。")
        return

    message = "RSS重点关键词:\n" + "\n".join(f"{index}. {keyword}" for index, keyword in enumerate(keywords, 1))
    send_group_message(group_id, message)


def _keyword_help_text() -> str:
    return (
        "RSS重点关键词命令:\n"
        "#rsskw list - 查看关键词\n"
        "#rsskw add <关键词1> [关键词2] ... - 添加关键词\n"
        "#rsskw del <关键词1> [关键词2] ... - 删除关键词\n"
        "#rsskw edit <旧关键词> <新关键词> - 修改关键词\n"
        "#rsskw set <关键词1> [关键词2] ... - 覆盖设置关键词\n"
        "#rsskw clear - 清空关键词"
    )
